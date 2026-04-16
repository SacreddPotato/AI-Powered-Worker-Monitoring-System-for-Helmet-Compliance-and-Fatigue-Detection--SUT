from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alert
from .serializers import AlertSerializer

class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.select_related('camera').all()
    serializer_class = AlertSerializer
    filterset_fields = ['camera', 'model_key', 'severity', 'status']

    @action(detail=True, methods=['patch'], url_path='acknowledge')
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.save()

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'alerts',
                {'type': 'alert.acknowledged', 'alert_id': alert.id}
            )

        return Response(AlertSerializer(alert).data)
