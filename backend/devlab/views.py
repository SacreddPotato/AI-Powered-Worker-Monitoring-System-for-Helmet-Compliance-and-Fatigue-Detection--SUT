import os
import time
import uuid
import threading
import cv2
import psutil
from django.conf import settings
from django.http import FileResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import DevImage, DevVideo
from .serializers import DevImageSerializer, DevVideoSerializer, ThresholdSerializer
from detection.services import get_inference_service, get_globally_enabled_model_keys, get_model_definitions

UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'dev_videos')


def _dev_image_dir():
    return os.path.join(settings.MEDIA_ROOT, 'dev_images')

@api_view(['POST', 'GET'])
def videos_list(request):
    if request.method == 'GET':
        videos = DevVideo.objects.all().order_by('-uploaded_at')
        return Response(DevVideoSerializer(videos, many=True).data)

    file = request.FILES.get('video')
    if not file:
        return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{file.name}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)

    cap = cv2.VideoCapture(filepath)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps > 0 else None
    cap.release()

    video = DevVideo.objects.create(
        original_filename=file.name,
        file_path=filepath,
        file_size=file.size,
        duration=duration,
    )
    return Response(DevVideoSerializer(video).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def video_file(request, video_id):
    video = DevVideo.objects.get(pk=video_id)
    return FileResponse(open(video.file_path, 'rb'), content_type='video/mp4')

@api_view(['GET'])
def video_stream(request, video_id):
    """Stream video as MJPEG.  With ?annotated=1 each frame is run through
    enabled models and bounding boxes / landmarks are drawn on top.

    Model loading happens in a background thread so the stream starts
    immediately with raw frames; annotations appear once models are ready.
    All frames are paced to the video's native FPS."""
    video = DevVideo.objects.get(pk=video_id)
    annotated = request.query_params.get('annotated', '0') == '1'
    overlays = request.query_params.get('overlays', '')

    def generate():
        from annotation import draw_annotations
        from detection.services import get_globally_enabled_model_keys

        cap = cv2.VideoCapture(video.file_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_delay = 1.0 / min(fps, 30)

        overlay_set = set(filter(None, overlays.split(','))) if overlays else None

        # Kick off model loading in background so raw frames stream immediately
        svc = get_inference_service() if annotated else None
        if svc and not svc.ready:
            threading.Thread(target=svc.preload, daemon=True).start()

        cached = {}
        enabled = set()
        frame_idx = 0
        INFER_EVERY = 3

        while cap.isOpened():
            frame_start = time.monotonic()

            ret, frame = cap.read()
            if not ret:
                break

            display = frame

            if annotated and svc and svc.ready:
                try:
                    import config as cfg
                    infer_every = INFER_EVERY if getattr(cfg, 'LOW_LATENCY_MODE', True) else 1
                    if frame_idx % infer_every == 0 or not cached:
                        enabled = get_globally_enabled_model_keys()
                        if enabled:
                            new = {}
                            for key in enabled:
                                new[key] = svc.run_inference_on_frame(key, frame, camera_id=0)
                            cached.clear()
                            cached.update(new)
                        else:
                            cached.clear()
                    if enabled and cached:
                        display = draw_annotations(frame, cached, enabled_overlays=overlay_set)
                except Exception:
                    pass

            _, buf = cv2.imencode('.jpg', display)
            if buf is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')

            # Always pace to real-time FPS, accounting for processing time
            elapsed = time.monotonic() - frame_start
            remaining = frame_delay - elapsed
            if remaining > 0:
                time.sleep(remaining)

            frame_idx += 1

        cap.release()

    return StreamingHttpResponse(
        generate(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

@api_view(['POST'])
def video_analyze(request, video_id):
    video = DevVideo.objects.get(pk=video_id)
    sample_every = int(request.data.get('sample_every_n_frames', 10))
    import config as cfg
    if not getattr(cfg, 'LOW_LATENCY_MODE', True):
        sample_every = 1
    max_samples = int(request.data.get('max_samples', 50))

    svc = get_inference_service()
    cap = cv2.VideoCapture(video.file_path)

    results = []
    frame_idx = 0
    samples = 0

    while cap.isOpened() and samples < max_samples:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every == 0:
            from detection.services import get_globally_enabled_model_keys
            enabled = get_globally_enabled_model_keys()
            frame_results = {}
            for key in enabled:
                result = svc.run_inference_on_frame(key, frame, camera_id=0)
                frame_results[key] = result
            results.append({'frame': frame_idx, 'detections': frame_results})
            samples += 1
        frame_idx += 1

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.release()
    return Response({
        'video_id': video.id,
        'fps': round(fps, 2),
        'frames_total': frame_idx,
        'frames_analyzed': samples,
        'results': results,
    })


@api_view(['POST', 'GET'])
def images_list(request):
    if request.method == 'GET':
        images = DevImage.objects.all().order_by('-uploaded_at')
        return Response(DevImageSerializer(images, many=True).data)

    file = request.FILES.get('image')
    if not file:
        return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

    upload_dir = _dev_image_dir()
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{file.name}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)

    frame = cv2.imread(filepath)
    if frame is None:
        try:
            os.remove(filepath)
        except OSError:
            pass
        return Response({'error': 'Uploaded file is not a readable image'}, status=status.HTTP_400_BAD_REQUEST)

    height, width = frame.shape[:2]
    image = DevImage.objects.create(
        original_filename=file.name,
        file_path=filepath,
        file_size=file.size,
        content_type=file.content_type or 'application/octet-stream',
        width=width,
        height=height,
    )
    return Response(DevImageSerializer(image).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def image_file(request, image_id):
    image = DevImage.objects.get(pk=image_id)
    return FileResponse(open(image.file_path, 'rb'), content_type=image.content_type or 'application/octet-stream')


@api_view(['POST'])
def image_analyze(request, image_id):
    image = DevImage.objects.get(pk=image_id)
    frame = cv2.imread(image.file_path)
    if frame is None:
        return Response({'error': 'Could not read image'}, status=status.HTTP_400_BAD_REQUEST)

    svc = get_inference_service()
    enabled = get_globally_enabled_model_keys()
    detections = {}
    for key in enabled:
        detections[key] = svc.run_inference_on_frame(key, frame, camera_id=0)

    height, width = frame.shape[:2]
    return Response({
        'image_id': image.id,
        'width': width,
        'height': height,
        'detections': detections,
    })

@api_view(['GET', 'PUT'])
def thresholds_view(request):
    import sys
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    import config as cfg
    from inference_device import resolve_inference_device

    def parse_bool(value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

    if request.method == 'GET':
        return Response({
            'confidence': cfg.DEFAULT_ALERT_CONFIDENCE_THRESHOLD,
            'fatigue_consecutive_frames': cfg.FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD,
            'ear_threshold': getattr(cfg, 'EAR_THRESHOLD', 0.21),
            'mar_threshold': getattr(cfg, 'MAR_THRESHOLD', 0.65),
            'head_tilt_degrees': cfg.HEAD_TILT_ALERT_DEGREES,
            'low_latency_mode': bool(getattr(cfg, 'LOW_LATENCY_MODE', True)),
            'temporal_smoothing_enabled': bool(getattr(cfg, 'TEMPORAL_SMOOTHING_ENABLED', False)),
            'temporal_smoothing_effective': bool(
                getattr(cfg, 'TEMPORAL_SMOOTHING_ENABLED', False)
                and not getattr(cfg, 'LOW_LATENCY_MODE', True)
            ),
            'inference_device': resolve_inference_device(),
        })

    data = request.data
    if 'confidence' in data:
        cfg.DEFAULT_ALERT_CONFIDENCE_THRESHOLD = float(data['confidence'])
    if 'fatigue_consecutive_frames' in data:
        cfg.FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD = int(data['fatigue_consecutive_frames'])
    if 'ear_threshold' in data:
        cfg.EAR_THRESHOLD = float(data['ear_threshold'])
    if 'mar_threshold' in data:
        cfg.MAR_THRESHOLD = float(data['mar_threshold'])
    if 'head_tilt_degrees' in data:
        cfg.HEAD_TILT_ALERT_DEGREES = float(data['head_tilt_degrees'])
    if 'low_latency_mode' in data:
        cfg.LOW_LATENCY_MODE = parse_bool(data['low_latency_mode'])
    if 'temporal_smoothing_enabled' in data:
        cfg.TEMPORAL_SMOOTHING_ENABLED = parse_bool(data['temporal_smoothing_enabled'])

    return Response({'status': 'updated'})

def _gpu_stats():
    """Get GPU utilisation via nvidia-smi (works reliably on Windows)."""
    try:
        import subprocess
        r = subprocess.run(
            ['nvidia-smi',
             '--query-gpu=utilization.gpu,memory.used,memory.total',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=3,
        )
        if r.returncode == 0:
            parts = r.stdout.strip().split(',')
            return {
                'gpu_available': True,
                'gpu_percent': float(parts[0].strip()),
                'gpu_mem_used_mb': round(float(parts[1].strip()), 0),
                'gpu_mem_total_mb': round(float(parts[2].strip()), 0),
            }
    except Exception:
        pass
    # Fallback: torch.cuda
    try:
        import torch
        if torch.cuda.is_available():
            pct = -1
            if hasattr(torch.cuda, 'utilization'):
                try:
                    pct = torch.cuda.utilization()
                except Exception:
                    pass
            return {
                'gpu_available': True,
                'gpu_percent': pct,
                'gpu_mem_used_mb': round(torch.cuda.memory_allocated() / 1024 / 1024, 0),
                'gpu_mem_total_mb': round(torch.cuda.get_device_properties(0).total_mem / 1024 / 1024, 0),
            }
    except Exception:
        pass
    return {'gpu_available': False, 'gpu_percent': -1, 'gpu_mem_used_mb': 0, 'gpu_mem_total_mb': 0}


@api_view(['GET'])
def performance_view(request):
    process = psutil.Process()
    mem = process.memory_info()
    gpu = _gpu_stats()

    return Response({
        'cpu_percent': psutil.cpu_percent(interval=0),
        'memory_mb': round(mem.rss / 1024 / 1024, 1),
        **gpu,
    })
