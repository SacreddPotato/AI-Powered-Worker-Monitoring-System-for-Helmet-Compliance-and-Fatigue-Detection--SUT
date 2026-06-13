from django.utils import timezone
from datetime import timedelta
import threading
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alert
from config import DEFAULT_ALERT_CONFIDENCE_THRESHOLD
from detection.models import Detection

SEVERITY_MAP = {
    'helmet': 'high',
    'fatigue': 'high',
    'vest': 'medium',
    'gloves': 'low',
    'goggles': 'low',
    'boots': 'medium',
    'faceshield': 'medium',
    'safetysuit': 'medium',
}

ALERT_COOLDOWN_SECONDS = 15
_smoothing_lock = threading.Lock()
_smoothing_state = {}


def _resolve_alert_severity(camera_id, model_key):
    from .models import CameraAlertSeverity

    override = CameraAlertSeverity.objects.filter(camera_id=camera_id, model_key=model_key).values_list('severity', flat=True).first()
    if override:
        return override
    return SEVERITY_MAP.get(model_key, 'low')


def _build_alert_message(model_key, payload):
    payload = payload or {}

    if model_key == 'fatigue':
        score = payload.get('hybrid_score')
        if isinstance(score, (int, float)):
            return f"Fatigue detected (score {float(score) * 100:.0f}%)"
        return "Fatigue detected"

    if model_key == 'helmet':
        missing = int(payload.get('no_helmet_count', 0) or 0)
        if missing > 0:
            return f"Helmet missing detected ({missing} worker{'s' if missing != 1 else ''})"
        return "Helmet compliance violation detected"

    if model_key in {'gloves', 'goggles', 'vest', 'boots', 'faceshield', 'safetysuit'}:
        missing = int(payload.get('missing_count', 0) or 0)
        if missing > 0:
            noun = {
                'gloves': 'gloves',
                'goggles': 'goggles',
                'vest': 'safety vest',
                'boots': 'safety boots',
                'faceshield': 'face shield',
                'safetysuit': 'safety suit',
            }[model_key]
            return f"Missing {noun} detected ({missing})"
        return f"{model_key.capitalize()} compliance violation detected"

    return f"{model_key.capitalize()} violation detected"


def _should_emit_alert(camera_id, model_key):
    since = timezone.now() - timedelta(seconds=ALERT_COOLDOWN_SECONDS)
    return not Alert.objects.filter(
        camera_id=camera_id,
        model_key=model_key,
        status='open',
        created_at__gte=since,
    ).exists()


def _temporal_smoothing_effective():
    import config as cfg

    return bool(
        getattr(cfg, 'TEMPORAL_SMOOTHING_ENABLED', False)
        and not getattr(cfg, 'LOW_LATENCY_MODE', True)
    )


def _reset_smoothing_state(camera_id, model_key):
    with _smoothing_lock:
        _smoothing_state.pop((camera_id, model_key), None)


def _passes_temporal_smoothing(camera_id, model_key):
    import config as cfg

    required = max(1, int(getattr(cfg, 'TEMPORAL_SMOOTHING_REQUIRED_FRAMES', 2)))
    stale_seconds = float(getattr(cfg, 'TEMPORAL_SMOOTHING_STALE_SECONDS', 5.0))
    now = timezone.now()
    key = (camera_id, model_key)

    with _smoothing_lock:
        state = _smoothing_state.get(key)
        count = 1
        if state is not None:
            last_seen = state.get('last_seen')
            if last_seen is not None and (now - last_seen).total_seconds() <= stale_seconds:
                count = int(state.get('count', 0)) + 1
        _smoothing_state[key] = {'count': count, 'last_seen': now}
        return count >= required

def create_alert(camera, model_key, message, detection=None, payload=None):
    severity = _resolve_alert_severity(camera.id, model_key)
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


def create_alert_from_inference(camera, model_key, result, detection=None):
    """Persist a Detection+Alert when a model reports an actionable event.
    Applies confidence threshold + cooldown to avoid duplicate spam."""
    if not result or result.get('status') != 'ok' or not bool(result.get('detected')):
        if _temporal_smoothing_effective():
            _reset_smoothing_state(camera.id, model_key)
        return None

    confidence = float(result.get('confidence') or 0.0)
    if confidence < DEFAULT_ALERT_CONFIDENCE_THRESHOLD and model_key != 'fatigue':
        return None

    if _temporal_smoothing_effective() and not _passes_temporal_smoothing(camera.id, model_key):
        return None

    if not _should_emit_alert(camera.id, model_key):
        return None

    payload = result.get('payload') or {}
    if detection is None:
        detection = Detection.objects.create(
            camera=camera,
            model_key=model_key,
            payload=payload,
            confidence=confidence,
            status=result.get('status', 'ok'),
            detected=bool(result.get('detected')),
        )

    message = _build_alert_message(model_key, payload)
    alert = create_alert(
        camera=camera,
        model_key=model_key,
        message=message,
        detection=detection,
        payload=payload,
    )
    if _temporal_smoothing_effective():
        _reset_smoothing_state(camera.id, model_key)
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
