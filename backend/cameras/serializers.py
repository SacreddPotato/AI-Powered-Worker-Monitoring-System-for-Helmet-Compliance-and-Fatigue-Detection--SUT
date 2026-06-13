from rest_framework import serializers
from .models import Camera, CountingZone

class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ['id', 'name', 'source_url', 'location', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class CountingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountingZone
        fields = ['id', 'camera', 'name', 'x1', 'y1', 'x2', 'y2', 'count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'camera', 'count', 'created_at', 'updated_at']

    def validate(self, attrs):
        # Merge with the existing instance so PATCH (partial) updates validate the
        # final rectangle, not just the changed corner.
        def resolved(field):
            if field in attrs:
                return attrs[field]
            if self.instance is not None:
                return getattr(self.instance, field)
            return None

        coords = {field: resolved(field) for field in ('x1', 'y1', 'x2', 'y2')}
        for field, value in coords.items():
            if value is None:
                raise serializers.ValidationError({field: 'This field is required.'})
            if not 0.0 <= float(value) <= 1.0:
                raise serializers.ValidationError(
                    {field: 'Coordinates must be normalized between 0 and 1.'}
                )

        if float(coords['x1']) >= float(coords['x2']):
            raise serializers.ValidationError({'x2': 'x2 must be greater than x1.'})
        if float(coords['y1']) >= float(coords['y2']):
            raise serializers.ValidationError({'y2': 'y2 must be greater than y1.'})
        return attrs
