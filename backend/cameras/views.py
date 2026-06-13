import threading
import cv2
from django.http import StreamingHttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Camera, CountingZone
from .serializers import CameraSerializer, CountingZoneSerializer
from .services import get_camera_service
from . import counting


def _make_annotator(camera_id, overlays_csv):
    """Return a function(frame)->frame that runs inference and draws
    annotations.  Results are cached and re-run every INFERENCE_INTERVAL
    frames.  Returns None while models are still loading (non-blocking)."""
    from detection.services import get_inference_service, get_effective_enabled_model_keys
    from cameras.models import Camera
    from alerts.services import create_alert_from_inference
    from annotation import draw_annotations
    from .inference_status import mark_loading, mark_disabled, mark_running, mark_error

    overlay_set = set(filter(None, overlays_csv.split(','))) if overlays_csv else None

    svc = get_inference_service()
    camera = Camera.objects.filter(pk=camera_id).first()

    # Kick off model loading in background so live frames are never blocked
    if not svc.ready:
        mark_loading(camera_id)
        threading.Thread(target=svc.preload, daemon=True).start()

    cached = {}
    counter = [0]
    INFERENCE_INTERVAL = 5

    def annotate(frame):
        # While models are still loading, return raw frame
        if not svc.ready:
            mark_loading(camera_id)
            return frame

        counter[0] += 1
        try:
            import config as cfg
            low_latency_mode = bool(getattr(cfg, 'LOW_LATENCY_MODE', True))
            inference_due = (
                counter[0] % INFERENCE_INTERVAL == 1
                if low_latency_mode
                else True
            )
            if inference_due or not cached:
                enabled = get_effective_enabled_model_keys(camera_id)
                if not enabled:
                    cached.clear()
                    mark_disabled(camera_id)
                    return frame
                new = {}
                for key in enabled:
                    new[key] = svc.run_inference_on_frame(key, frame, camera_id=camera_id)
                if camera is not None:
                    for key, result in new.items():
                        create_alert_from_inference(camera=camera, model_key=key, result=result)
                detected_count = sum(1 for item in new.values() if bool(item.get('detected')))
                mark_running(camera_id, model_keys=enabled, detected_count=detected_count)
                cached.clear()
                cached.update(new)
            return draw_annotations(frame, cached, enabled_overlays=overlay_set)
        except Exception:
            mark_error(camera_id, 'inference_exception')
            return frame  # raw frame on any inference error

    return annotate


@api_view(['GET', 'POST'])
def camera_zones_view(request, camera_id):
    """List counting zones for a camera, or create a new one."""
    try:
        camera = Camera.objects.get(pk=camera_id)
    except Camera.DoesNotExist:
        return Response({'error': 'Camera not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        zones = CountingZone.objects.filter(camera=camera)
        return Response(CountingZoneSerializer(zones, many=True).data)

    serializer = CountingZoneSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    zone = serializer.save(camera=camera)
    return Response(CountingZoneSerializer(zone).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def camera_zone_detail_view(request, camera_id, zone_id):
    """Retrieve, update, or delete a single counting zone."""
    try:
        zone = CountingZone.objects.get(pk=zone_id, camera_id=camera_id)
    except CountingZone.DoesNotExist:
        return Response({'error': 'Counting zone not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        zone.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if request.method == 'GET':
        return Response(CountingZoneSerializer(zone).data)

    partial = request.method == 'PATCH'
    serializer = CountingZoneSerializer(zone, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(CountingZoneSerializer(zone).data)


@api_view(['POST'])
def camera_zone_reset_view(request, camera_id, zone_id):
    """Reset a counting zone's cumulative count back to zero."""
    try:
        zone = CountingZone.objects.get(pk=zone_id, camera_id=camera_id)
    except CountingZone.DoesNotExist:
        return Response({'error': 'Counting zone not found'}, status=status.HTTP_404_NOT_FOUND)

    zone.count = 0
    zone.save(update_fields=['count', 'updated_at'])
    counting.reset_zone(int(camera_id), int(zone_id))
    return Response(CountingZoneSerializer(zone).data)


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
    def inference(self, request, pk=None):
        from .inference_status import get_inference_status

        camera = self.get_object()
        return Response(get_inference_status(camera.id))

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
