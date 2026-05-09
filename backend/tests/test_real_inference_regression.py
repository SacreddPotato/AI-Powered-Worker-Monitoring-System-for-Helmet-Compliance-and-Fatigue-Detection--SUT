import pytest

from conftest import EXPECTED_MODEL_KEYS
from scripts.snapshot_models import verify_snapshot


@pytest.mark.ml
@pytest.mark.slow
@pytest.mark.regression
def test_all_configured_models_have_weights(real_inference_service):
    from config import MODEL_DEFINITIONS

    assert real_inference_service is not None
    missing = []
    for model_key, definition in MODEL_DEFINITIONS.items():
        for field in ("weights_path", "person_model_path", "face_landmarker_path"):
            path = definition.get(field)
            if path:
                import os

                if not os.path.exists(path):
                    missing.append(f"{model_key}:{field}:{path}")

    assert missing == []


@pytest.fixture(scope="session")
def real_inference_service():
    verify_snapshot()
    from config import MODEL_DEFINITIONS
    from inference_service import InferenceService

    return InferenceService(MODEL_DEFINITIONS)


@pytest.mark.ml
@pytest.mark.slow
@pytest.mark.regression
@pytest.mark.parametrize("model_key", EXPECTED_MODEL_KEYS)
def test_all_configured_models_run_real_inference(real_inference_service, blank_frame, model_key):
    results = real_inference_service.run_models(blank_frame, [model_key], camera_id=42)

    assert len(results) == 1
    result = results[0]
    assert result["model_key"] == model_key
    assert isinstance(result["model_name"], str) and result["model_name"]
    assert result["status"] in {"ok", "no_face", "error", "unavailable"}
    assert isinstance(result["detected"], bool)
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["payload"], dict)


@pytest.mark.ml
@pytest.mark.slow
@pytest.mark.regression
def test_model_payload_contracts(real_inference_service, blank_frame):
    results = {
        item["model_key"]: item
        for item in real_inference_service.run_models(blank_frame, list(EXPECTED_MODEL_KEYS), camera_id=42)
    }

    helmet_payload = results["helmet"]["payload"]
    assert {"person_count", "helmet_count", "no_helmet_count", "classification", "boxes"}.issubset(helmet_payload)

    fatigue_payload = results["fatigue"]["payload"]
    assert {"status", "fatigue_probability", "ear", "mar", "head_tilt_degrees", "hybrid_score"}.issubset(fatigue_payload)

    vest_payload = results["vest"]["payload"]
    assert "vest_id" in vest_payload or results["vest"]["status"] != "ok"

    for model_key in ("vest", "gloves", "goggles", "boots", "faceshield", "safetysuit"):
        payload = results[model_key]["payload"]
        if results[model_key]["status"] == "ok":
            assert {"count", "missing_count", "ok_count", "classification", "boxes", "matched_target_labels"}.issubset(payload)


@pytest.mark.ml
@pytest.mark.slow
@pytest.mark.regression
@pytest.mark.parametrize("model_key", EXPECTED_MODEL_KEYS)
def test_negative_fixtures_do_not_crash(real_inference_service, blank_frame, model_key):
    result = real_inference_service.run_models(blank_frame, [model_key], camera_id=99)[0]

    assert result["status"] in {"ok", "no_face", "unavailable"}
    assert "Traceback" not in str(result["payload"])


@pytest.mark.regression
def test_fatigue_consecutive_frame_regression(monkeypatch):
    import inference_service as inference_module
    from inference_service import FatigueModelAdapter

    class FakeEngine:
        def analyze(self, frame):
            return {
                "status": "ok",
                "fatigue_probability": 0.9,
                "ear": 0.1,
                "mar": 0.2,
                "head_tilt_degrees": 0.0,
                "hybrid_score": 0.9,
                "is_fatigued": True,
                "forced_fatigue_state": False,
                "head_tilt_exceeded": False,
            }

    monkeypatch.setattr(inference_module, "FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD", 3)
    adapter = FatigueModelAdapter.__new__(FatigueModelAdapter)
    adapter.available = True
    adapter._engine = FakeEngine()
    adapter._fatigue_consecutive_by_camera = {}

    outputs = [adapter.infer(frame=None, camera_id=7) for _ in range(3)]

    assert [item["payload"]["consecutive_fatigue_frames"] for item in outputs] == [1, 2, 3]
    assert outputs[0]["detected"] is False
    assert outputs[1]["detected"] is False
    assert outputs[2]["detected"] is True
    assert "sustained_fatigue" in outputs[2]["payload"]["trigger_reason"]
