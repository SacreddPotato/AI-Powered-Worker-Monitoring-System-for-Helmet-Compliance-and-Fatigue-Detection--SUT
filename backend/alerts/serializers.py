from rest_framework import serializers
from .models import Alert

class AlertSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source='camera.name', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'detection', 'camera', 'camera_name', 'model_key',
            'severity', 'status', 'message', 'payload',
            'created_at', 'acknowledged_at',
        ]
