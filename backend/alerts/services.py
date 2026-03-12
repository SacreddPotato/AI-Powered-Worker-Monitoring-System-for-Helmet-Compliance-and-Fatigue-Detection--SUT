from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alert

SEVERITY_MAP = {
    'helmet': 'high',
    'fatigue': 'high',
    'vest': 'medium',
    'gloves': 'low',
    'goggles': 'low',
}

def create_alert(camera, model_key, message, detection=None, payload=None):
    severity = SEVERITY_MAP.get(model_key, 'low')
    alert = Alert.objects.create(
        detection=detection,
        camera=camera,
        model_key=model_key,
        severity=severity,
        message=message,
        payload=payload or {},
    )
    broadcast_alert(alert)
    return alert

def broadcast_alert(alert):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        'alerts',
        {
            'type': 'alert.new',
            'alert': {
                'id': alert.id,
                'severity': alert.severity,
                'model_key': alert.model_key,
                'camera_id': alert.camera_id,
                'camera_name': alert.camera.name,
                'message': alert.message,
                'payload': alert.payload,
                'status': alert.status,
                'created_at': alert.created_at.isoformat(),
            }
        }
    )
