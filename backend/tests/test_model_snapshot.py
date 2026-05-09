import json
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = [pytest.mark.ml, pytest.mark.slow, pytest.mark.regression]


def test_model_snapshot_manifest_matches_configured_artifacts(root_dir):
    snapshot_path = root_dir / "backend" / "ml_models" / "model_snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert snapshot["schema_version"] == 1
    artifact_paths = {item["path"] for item in snapshot["artifacts"]}

    from config import MODEL_DEFINITIONS

    expected_paths = set()
    for definition in MODEL_DEFINITIONS.values():
        for field in ("weights_path", "person_model_path", "face_landmarker_path"):
            if definition.get(field):
                expected_paths.add(
                    Path(definition[field]).resolve().relative_to(root_dir).as_posix()
                )

    assert artifact_paths == expected_paths
    for artifact in snapshot["artifacts"]:
        assert artifact["size_bytes"] > 0
        assert len(artifact["sha256"]) == 64
        assert artifact["model_key_refs"]


def test_snapshot_verify_command_passes(root_dir):
    result = subprocess.run(
        [sys.executable, "scripts/snapshot_models.py", "verify"],
        cwd=root_dir,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "snapshot verified" in result.stdout.lower()


def test_snapshot_script_is_app_free(root_dir):
    script_text = (root_dir / "scripts" / "snapshot_models.py").read_text(encoding="utf-8")

    forbidden_imports = ["django", "inference_service", "ultralytics", "torch", "cv2"]
    for forbidden in forbidden_imports:
        assert forbidden not in script_text
