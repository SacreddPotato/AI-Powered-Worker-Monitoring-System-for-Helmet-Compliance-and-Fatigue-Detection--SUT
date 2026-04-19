import threading
import cv2
from django.http import StreamingHttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Camera
from .serializers import CameraSerializer
from .services import get_camera_service


def _make_annotator(camera_id, overlays_csv):
    """Return a function(frame)->frame that runs inference and draws
    annotations.  Results are cached and re-run every INFERENCE_INTERVAL
    frames.  Returns None while models are still loading (non-blocking)."""
    from detection.services import get_inference_service, get_effective_enabled_model_keys
    from cameras.models import Camera
    from alerts.services import create_alert_from_inference
    from annotation import draw_annotations

    overlay_set = set(filter(None, overlays_csv.split(','))) if overlays_csv else None

    svc = get_inference_service()
    camera = Camera.objects.filter(pk=camera_id).first()

    # Kick off model loading in background so live frames are never blocked
    if not svc.ready:
        threading.Thread(target=svc.preload, daemon=True).start()

    cached = {}
    counter = [0]
    INFERENCE_INTERVAL = 5

    def annotate(frame):
        # While models are still loading, return raw frame
        if not svc.ready:
            return frame

        counter[0] += 1
        try:
            if counter[0] % INFERENCE_INTERVAL == 1 or not cached:
                enabled = get_effective_enabled_model_keys(camera_id)
                if not enabled:
                    cached.clear()
                    return frame
                new = {}
                for key in enabled:
                    new[key] = svc.run_inference_on_frame(key, frame, camera_id=camera_id)
                if camera is not None:
                    for key, result in new.items():
                        create_alert_from_inference(camera=camera, model_key=key, result=result)
                cached.clear()
                cached.update(new)
            return draw_annotations(frame, cached, enabled_overlays=overlay_set)
        except Exception:
            return frame  # raw frame on any inference error

    return annotate


class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer

    @action(detail=False, methods=['post'])
    def probe(self, request):
        """Test a source URL and return a single JPEG preview frame.
        Body: {"source_url": "rtsp://... or 0"}
        Returns JPEG image if successful, 422 if unreachable."""
        from django.http import HttpResponse
        source_url = request.data.get('source_url', '')
        if not source_url:
            return Response({'error': 'source_url required'}, status=400)
        svc = get_camera_service()
        frame, error = svc.probe_source(source_url)
        if frame is None:
            return Response({'error': error or 'Could not read frame from source'}, status=422)

        ok, jpeg = cv2.imencode('.jpg', frame)
        if not ok or jpeg is None:
            return Response({'error': 'Could not encode probe frame'}, status=500)

        return HttpResponse(jpeg.tobytes(), content_type='image/jpeg')

    @action(detail=False, methods=['get'])
    def discover(self, request):
        """Enumerate system video capture devices (webcams etc.)."""
        svc = get_camera_service()
        devices = svc.discover_devices()
        return Response(devices)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        camera = self.get_object()
        svc = get_camera_service()
        result = svc.check_camera_status(camera.source_url)
        return Response(result)

    @action(detail=True, methods=['get'])
    def snapshot(self, request, pk=None):
        """Return a single JPEG frame — useful for testing camera connectivity."""
        from django.http import HttpResponse
        camera = self.get_object()
        svc = get_camera_service()
        for frame_bytes in svc.stream_frames(camera.source_url, camera.id):
            return HttpResponse(frame_bytes, content_type='image/jpeg')
        return HttpResponse(status=502)

    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        camera = self.get_object()
        annotated = request.query_params.get('annotated', '0') == '1'
        overlays = request.query_params.get('overlays', '')
        svc = get_camera_service()

        annotate_fn = None
        if annotated:
            annotate_fn = _make_annotator(camera.id, overlays)

        def generate():
            for frame_bytes in svc.stream_frames(camera.source_url, camera.id, annotate_fn=annotate_fn):
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        response = StreamingHttpResponse(
            generate(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['X-Accel-Buffering'] = 'no'
        response['Connection'] = 'keep-alive'
        return response
