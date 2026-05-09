import json
from pathlib import Path

import cv2
import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
EXPECTED_MODEL_KEYS = (
    "helmet",
    "fatigue",
    "vest",
    "gloves",
    "goggles",
    "boots",
    "faceshield",
    "safetysuit",
)


@pytest.fixture(scope="session")
def root_dir():
    return ROOT


@pytest.fixture(scope="session")
def fixture_metadata():
    metadata_path = BACKEND_DIR / "tests" / "fixtures" / "media" / "fixtures.json"
    return json.loads(metadata_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def blank_frame(fixture_metadata):
    image_path = BACKEND_DIR / fixture_metadata["negative"]["path"]
    frame = cv2.imread(str(image_path))
    assert frame is not None, f"Could not read fixture image: {image_path}"
    return frame
