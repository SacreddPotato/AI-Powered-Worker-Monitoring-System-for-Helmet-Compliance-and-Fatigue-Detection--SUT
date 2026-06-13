import pytest


def _detected_result():
    return {
        "status": "ok",
        "detected": True,
        "confidence": 0.9,
        "payload": {"no_helmet_count": 1, "classification": "helmet_missing"},
    }


@pytest.mark.django_db
def test_low_latency_mode_ignores_temporal_smoothing(monkeypatch):
    import config
    import alerts.services as alert_services
    from cameras.models import Camera

    monkeypatch.setattr(config, "LOW_LATENCY_MODE", True, raising=False)
    monkeypatch.setattr(config, "TEMPORAL_SMOOTHING_ENABLED", True, raising=False)
    monkeypatch.setattr(alert_services, "DEFAULT_ALERT_CONFIDENCE_THRESHOLD", 0.1)

    camera = Camera.objects.create(name="Gate 0", source_url="0", location="Yard")

    assert alert_services.create_alert_from_inference(camera, "helmet", _detected_result()) is not None


@pytest.mark.django_db
def test_disabled_temporal_smoothing_allows_single_alert(monkeypatch):
    import config
    import alerts.services as alert_services
    from cameras.models import Camera

    monkeypatch.setattr(config, "LOW_LATENCY_MODE", False, raising=False)
    monkeypatch.setattr(config, "TEMPORAL_SMOOTHING_ENABLED", False, raising=False)
    monkeypatch.setattr(alert_services, "DEFAULT_ALERT_CONFIDENCE_THRESHOLD", 0.1)

    camera = Camera.objects.create(name="Gate 0B", source_url="0", location="Yard")

    assert alert_services.create_alert_from_inference(camera, "helmet", _detected_result()) is not None


@pytest.mark.django_db
def test_temporal_smoothing_requires_two_consecutive_detections(monkeypatch):
    import config
    import alerts.services as alert_services
    from alerts.models import Alert
    from cameras.models import Camera

    monkeypatch.setattr(config, "LOW_LATENCY_MODE", False, raising=False)
    monkeypatch.setattr(config, "TEMPORAL_SMOOTHING_ENABLED", True, raising=False)
    monkeypatch.setattr(alert_services, "DEFAULT_ALERT_CONFIDENCE_THRESHOLD", 0.1)

    camera = Camera.objects.create(name="Gate 1", source_url="0", location="Yard")
    result = _detected_result()

    first = alert_services.create_alert_from_inference(camera, "helmet", result)
    second = alert_services.create_alert_from_inference(camera, "helmet", result)

    assert first is None
    assert second is not None
    assert Alert.objects.filter(camera=camera, model_key="helmet").count() == 1


@pytest.mark.django_db
def test_temporal_smoothing_resets_on_clear_frame(monkeypatch):
    import config
    import alerts.services as alert_services
    from alerts.models import Alert
    from cameras.models import Camera

    monkeypatch.setattr(config, "LOW_LATENCY_MODE", False, raising=False)
    monkeypatch.setattr(config, "TEMPORAL_SMOOTHING_ENABLED", True, raising=False)
    monkeypatch.setattr(alert_services, "DEFAULT_ALERT_CONFIDENCE_THRESHOLD", 0.1)

    camera = Camera.objects.create(name="Gate 2", source_url="0", location="Yard")
    detected = _detected_result()
    clear = {
        "status": "ok",
        "detected": False,
        "confidence": 0.0,
        "payload": {"classification": "helmet_ok"},
    }

    assert alert_services.create_alert_from_inference(camera, "helmet", detected) is None
    assert alert_services.create_alert_from_inference(camera, "helmet", clear) is None
    assert alert_services.create_alert_from_inference(camera, "helmet", detected) is None
    assert Alert.objects.filter(camera=camera, model_key="helmet").count() == 0
