from rest_framework import serializers
from .models import DevVideo

class DevVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DevVideo
        fields = ['id', 'original_filename', 'file_size', 'duration', 'uploaded_at']

class ThresholdSerializer(serializers.Serializer):
    confidence = serializers.FloatField(required=False)
    fatigue_consecutive_frames = serializers.IntegerField(required=False)
    ear_threshold = serializers.FloatField(required=False)
    mar_threshold = serializers.FloatField(required=False)
    head_tilt_degrees = serializers.FloatField(required=False)
