from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ModelSetting, CameraModel, Detection
from .serializers import ModelSettingSerializer, CameraModelSerializer, DetectionSerializer
from .services import get_inference_service, get_model_definitions
from cameras.models import Camera

class ModelSettingViewSet(viewsets.ModelViewSet):
    queryset = ModelSetting.objects.all()
    serializer_class = ModelSettingSerializer
    lookup_field = 'key'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        is_enabled = request.data.get('enabled', request.data.get('is_enabled'))
        if is_enabled is not None:
            instance.is_enabled = bool(is_enabled)
            instance.save()
        return Response(ModelSettingSerializer(instance).data)

@api_view(['GET', 'PUT'])
def camera_models_view(request, camera_id, model_key=None):
    camera = Camera.objects.get(pk=camera_id)

    if model_key is None:
        overrides = CameraModel.objects.filter(camera=camera).select_related('model_setting')
        return Response(CameraModelSerializer(overrides, many=True).data)

    model_setting = ModelSetting.objects.get(key=model_key)
    override, _ = CameraModel.objects.get_or_create(camera=camera, model_setting=model_setting)
    is_enabled = request.data.get('enabled', request.data.get('is_enabled'))
    if is_enabled is not None:
        override.is_enabled = bool(is_enabled)
        override.save()
    return Response(CameraModelSerializer(override).data)

@api_view(['POST'])
def analyze_frame(request):
    camera_id = request.data.get('camera_id')
    if not camera_id:
        return Response({'error': 'camera_id required'}, status=status.HTTP_400_BAD_REQUEST)

    camera = Camera.objects.get(pk=camera_id)
    svc = get_inference_service()

    enabled = ModelSetting.objects.filter(is_enabled=True).values_list('key', flat=True)
    overrides = CameraModel.objects.filter(camera=camera).select_related('model_setting')
    override_map = {o.model_setting.key: o.is_enabled for o in overrides}

    results = []
    for key in enabled:
        if not override_map.get(key, True):
            continue
        result = svc.run_inference(key, camera.source_url, camera.id)
        det = Detection.objects.create(
            camera=camera,
            model_key=key,
            payload=result.get('payload', {}),
            confidence=result.get('confidence', 0.0),
            status=result.get('status', 'ok'),
            detected=result.get('detected', False),
        )
        results.append(DetectionSerializer(det).data)

    return Response(results)

class DetectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Detection.objects.all()
    serializer_class = DetectionSerializer
    filterset_fields = ['camera', 'model_key', 'status']
