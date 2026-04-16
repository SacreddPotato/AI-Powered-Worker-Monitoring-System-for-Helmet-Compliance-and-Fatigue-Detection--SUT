from rest_framework import serializers
from .models import ModelSetting, CameraModel, Detection

class ModelSettingSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    health = serializers.SerializerMethodField()

    class Meta:
        model = ModelSetting
        fields = ['key', 'is_enabled', 'display_name', 'description', 'health']

    def get_display_name(self, obj):
        from .services import get_model_definitions
        defn = get_model_definitions().get(obj.key, {})
        return defn.get('display_name', obj.key)

    def get_description(self, obj):
        from .services import get_model_definitions
        defn = get_model_definitions().get(obj.key, {})
        return defn.get('description', '')

    def get_health(self, obj):
<<<<<<< HEAD
        request = self.context.get('request')
        include_health = bool(request and request.query_params.get('include_health') in {'1', 'true', 'True'})
        if not include_health:
            return None
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
        from .services import get_inference_service
        svc = get_inference_service()
        return svc.get_model_health(obj.key)

class CameraModelSerializer(serializers.ModelSerializer):
    model_key = serializers.CharField(source='model_setting.key', read_only=True)

    class Meta:
        model = CameraModel
        fields = ['id', 'model_key', 'is_enabled']

class DetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detection
        fields = ['id', 'camera', 'model_key', 'payload', 'confidence', 'status', 'detected', 'created_at']
