import pytest


@pytest.mark.django_db
def test_health_endpoint_reports_ok(client):
    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.django_db
def test_camera_crud_and_model_override_flow(client):
    from detection.models import ModelSetting

    ModelSetting.objects.get_or_create(key="helmet", defaults={"is_enabled": True})

    create_response = client.post(
        "/api/v1/cameras/",
        {"name": "Gate 1", "source_url": "0", "location": "Yard", "is_active": True},
        content_type="application/json",
    )
    assert create_response.status_code == 201
    camera_id = create_response.json()["id"]

    assert client.get("/api/v1/cameras/").status_code == 200

    override_response = client.put(
        f"/api/v1/cameras/{camera_id}/models/helmet/",
        {"enabled": False},
        content_type="application/json",
    )
    assert override_response.status_code == 200
    assert override_response.json()["model_key"] == "helmet"
    assert override_response.json()["is_enabled"] is False


@pytest.mark.django_db
def test_model_list_and_alert_severity_matrix(client):
    from cameras.models import Camera
    from detection.models import ModelSetting

    Camera.objects.create(name="Gate 1", source_url="0", location="Yard")
    ModelSetting.objects.get_or_create(key="helmet", defaults={"is_enabled": True})

    models_response = client.get("/api/v1/models/")
    assert models_response.status_code == 200
    model_payload = models_response.json()
    model_items = model_payload["results"] if isinstance(model_payload, dict) else model_payload
    assert any(item["key"] == "helmet" for item in model_items)

    severity_response = client.get("/api/v1/alerts/severity/matrix/")
    assert severity_response.status_code == 200
    assert "helmet" in severity_response.json()["model_keys"]


@pytest.mark.django_db
def test_thresholds_endpoint_roundtrip(client):
    response = client.get("/api/v1/dev/thresholds/")
    assert response.status_code == 200
    assert "confidence" in response.json()

    update = client.put(
        "/api/v1/dev/thresholds/",
        {"confidence": 0.52, "fatigue_consecutive_frames": 4},
        content_type="application/json",
    )
    assert update.status_code == 200
    assert update.json()["status"] == "updated"


@pytest.mark.django_db
def test_detection_analyze_persists_with_fake_inference(client, monkeypatch):
    from cameras.models import Camera
    from detection.models import Detection, ModelSetting
    import detection.views as detection_views

    camera = Camera.objects.create(name="Gate 1", source_url="0", location="Yard")
    ModelSetting.objects.get_or_create(key="helmet", defaults={"is_enabled": True})

    class FakeInferenceService:
        def run_inference(self, model_key, source_url, camera_id=0):
            return {
                "status": "ok",
                "detected": False,
                "confidence": 0.0,
                "payload": {"classification": "helmet_ok", "camera_id": camera_id},
            }

    monkeypatch.setattr(detection_views, "get_inference_service", lambda: FakeInferenceService())

    response = client.post(
        "/api/v1/detections/analyze/",
        {"camera_id": camera.id},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert Detection.objects.filter(camera=camera, model_key="helmet").exists()
