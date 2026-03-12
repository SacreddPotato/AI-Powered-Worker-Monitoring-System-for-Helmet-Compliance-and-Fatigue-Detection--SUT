import cv2
from django.http import StreamingHttpResponse, JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Camera
from .serializers import CameraSerializer
from .services import get_camera_service

class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        camera = self.get_object()
        svc = get_camera_service()
        result = svc.check_camera_status(camera.source_url)
        return Response(result)

    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        camera = self.get_object()
        annotated = request.query_params.get('annotated', '0') == '1'
        svc = get_camera_service()

        def generate():
            for frame_bytes in svc.stream_frames(camera.source_url, camera.id, annotated=annotated):
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        return StreamingHttpResponse(
            generate(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
