import os
import time
import uuid
import cv2
import psutil
from django.conf import settings
from django.http import FileResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import DevVideo
from .serializers import DevVideoSerializer, ThresholdSerializer
from detection.services import get_inference_service, get_model_definitions

UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'dev_videos')

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
    video = DevVideo.objects.get(pk=video_id)
    annotated = request.query_params.get('annotated', '0') == '1'

    def generate():
        cap = cv2.VideoCapture(video.file_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            _, buf = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        cap.release()

    return StreamingHttpResponse(
        generate(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

@api_view(['POST'])
def video_analyze(request, video_id):
    video = DevVideo.objects.get(pk=video_id)
    sample_every = int(request.data.get('sample_every_n_frames', 10))
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
            from detection.models import ModelSetting
            enabled = ModelSetting.objects.filter(is_enabled=True).values_list('key', flat=True)
            frame_results = {}
            for key in enabled:
                result = svc.run_inference_on_frame(key, frame, camera_id=0)
                frame_results[key] = result
            results.append({'frame': frame_idx, 'detections': frame_results})
            samples += 1
        frame_idx += 1

    cap.release()
    return Response({
        'video_id': video.id,
        'frames_total': frame_idx,
        'frames_analyzed': samples,
        'results': results,
    })

@api_view(['GET', 'PUT'])
def thresholds_view(request):
    import sys
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    import config as cfg

    if request.method == 'GET':
        return Response({
            'confidence': cfg.DEFAULT_ALERT_CONFIDENCE_THRESHOLD,
            'fatigue_consecutive_frames': cfg.FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD,
            'ear_threshold': getattr(cfg, 'EAR_THRESHOLD', 0.21),
            'mar_threshold': getattr(cfg, 'MAR_THRESHOLD', 0.65),
            'head_tilt_degrees': cfg.HEAD_TILT_ALERT_DEGREES,
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

    return Response({'status': 'updated'})

@api_view(['GET'])
def performance_view(request):
    import torch
    gpu_available = torch.cuda.is_available()
    gpu_percent = 0
    if gpu_available:
        try:
            gpu_percent = torch.cuda.utilization()
        except Exception:
            gpu_percent = -1

    process = psutil.Process()
    mem = process.memory_info()

    return Response({
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_mb': round(mem.rss / 1024 / 1024, 1),
        'gpu_available': gpu_available,
        'gpu_percent': gpu_percent,
    })
