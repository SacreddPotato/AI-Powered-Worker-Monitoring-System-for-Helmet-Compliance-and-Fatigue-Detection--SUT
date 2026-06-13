import importlib.util
from pathlib import Path


def _load_generator(root_dir):
    script_path = root_dir / "scripts" / "generate_model_output_examples.py"
    spec = importlib.util.spec_from_file_location("generate_model_output_examples", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generator_declares_expected_model_output_contract(root_dir):
    generator = _load_generator(root_dir)

    assert generator.MODEL_KEYS == (
        "helmet",
        "vest",
        "gloves",
        "goggles",
        "boots",
        "faceshield",
        "safetysuit",
        "fatigue",
    )
    assert generator.EXAMPLE_FILENAMES == ("positive.jpg", "negative.jpg", "contact_sheet.jpg")
    assert generator.OUTPUT_ROOT == root_dir / "docs" / "model_output_examples"
    assert generator.CURATED_MODEL_KEYS == ("gloves", "boots", "goggles", "faceshield")


def test_manifest_validation_rejects_missing_example_file(root_dir, tmp_path):
    generator = _load_generator(root_dir)
    manifest = {
        "models": {
            "helmet": {
                "positive": {"path": str(tmp_path / "missing.jpg")},
                "negative": {"path": str(tmp_path / "also-missing.jpg")},
                "contact_sheet": {"path": str(tmp_path / "sheet.jpg")},
            }
        }
    }

    missing = generator.missing_manifest_files(manifest)

    assert missing == [
        str(tmp_path / "missing.jpg"),
        str(tmp_path / "also-missing.jpg"),
        str(tmp_path / "sheet.jpg"),
    ]


def test_curated_source_specs_cover_weak_ppe_models(root_dir):
    generator = _load_generator(root_dir)

    specs_by_model = {}
    for spec in generator.CURATED_SOURCE_SPECS:
        specs_by_model.setdefault(spec["model_key"], []).append(spec)
        for field in ("kind", "slug", "page_url", "license", "description"):
            assert spec[field]

    for model_key in generator.CURATED_MODEL_KEYS:
        assert any(spec["kind"] == "positive" for spec in specs_by_model[model_key])


def test_fatigue_labels_do_not_call_monitoring_frames_alert(root_dir):
    generator = _load_generator(root_dir)

    assert generator.fatigue_state_label({"is_fatigued": False}) == "NOT FATIGUED"
    assert generator.fatigue_state_label({"is_fatigued": True}) == "FATIGUED"
