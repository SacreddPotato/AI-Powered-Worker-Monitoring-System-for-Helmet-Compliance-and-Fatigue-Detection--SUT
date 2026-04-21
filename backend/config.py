import shutil
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
DATABASE_PATH = BASE_DIR / "monitoring.db"
UPLOADS_DIR = BASE_DIR / "uploads"
DEV_VIDEO_DIR = UPLOADS_DIR / "dev_videos"
ML_MODELS_DIR = BASE_DIR / "ml_models"

MODEL_DEFINITIONS = {
    "helmet": {
        "display_name": "Helmet Detection",
        "description": "Detects workers missing helmets using helmet + upper-body detection.",
        "weights_path": str(ML_MODELS_DIR / "best.pt"),
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "target_labels": ["no-hardhat", "no_helmet", "no-helmet", "no hardhat"],
        "strict_target_match": False,
    },
    "fatigue": {
        "display_name": "Fatigue Detection",
        "description": "Hybrid fatigue scoring with Swin model + EAR/MAR + head tilt alerts.",
        "weights_path": str(ML_MODELS_DIR / "swin_best.pth"),
        "shape_predictor_path": str(ML_MODELS_DIR / "shape_predictor_68_face_landmarks.dat"),
    },
    "vest": {
        "display_name": "Vest Detection",
        "description": "Detects high-visibility safety vests and reads vest QR IDs.",
        "weights_path": str(ML_MODELS_DIR / "vest_detection.pt"),
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "target_labels": ["vest", "safety vest", "safety_vest", "safety-vest"],
    },
    "gloves": {
        "display_name": "Gloves Detection",
        "description": "Detects worker safety gloves.",
        "weights_path": str(ML_MODELS_DIR / "gloves_detection.pt"),
        "target_labels": ["glove", "gloves", "no_glove", "no-glove"],
    },
    "goggles": {
        "display_name": "Goggles Detection",
        "description": "Detects protective eyewear (goggles).",
        "weights_path": str(ML_MODELS_DIR / "goggles_detection.pt"),
        "target_labels": ["goggles", "goggle", "no_goggles", "no-goggles"],
    },
    "boots": {
        "display_name": "Boot Detection",
        "description": "Detects worker safety boots from MediaPipe foot regions using Ultralytics pretrained weights.",
        "weights_path": str(ML_MODELS_DIR / "boots_detection.pt"),
        "target_labels": [
            "boot",
            "boots",
            "safety boot",
            "safety boots",
            "running shoe",
            "cowboy boot",
            "sandal",
            "loafer",
            "slipper",
            "sneaker",
            "work boot",
            "hiking boot",
            "no_boot",
            "no-boots",
            "no boots",
        ],
        "strict_target_match": False,
    },
    "faceshield": {
        "display_name": "Face Shield Detection",
        "description": "Detects protective face shields.",
        "weights_path": str(ML_MODELS_DIR / "faceshield_detection.pt"),
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "target_labels": ["face shield", "faceshield", "shield", "no_face_shield", "no-faceshield", "no shield"],
        "strict_target_match": False,
    },
    "safetysuit": {
        "display_name": "Safety Suit Detection",
        "description": "Detects protective safety suits/coveralls.",
        "weights_path": str(ML_MODELS_DIR / "safety_suit_detection.pt"),
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "target_labels": ["safety suit", "safetysuit", "coverall", "protective suit", "no_safety_suit", "no safety suit"],
        "strict_target_match": False,
    },
}

DEFAULT_ALERT_CONFIDENCE_THRESHOLD = 0.45
FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD = 8
HEAD_TILT_ALERT_DEGREES = 15.0


def get_required_model_paths() -> List[Path]:
    required_paths = set()
    for model_info in MODEL_DEFINITIONS.values():
        for field_name in ("weights_path", "person_model_path", "shape_predictor_path"):
            field_value = model_info.get(field_name)
            if not field_value:
                continue
            required_paths.add(Path(field_value))
    return sorted(required_paths)


def get_missing_model_files() -> List[str]:
    missing_files = []
    for path in get_required_model_paths():
        if path.exists():
            continue
        try:
            relative_path = path.relative_to(BASE_DIR)
        except ValueError:
            relative_path = path
        missing_files.append(str(relative_path).replace("\\", "/"))
    return missing_files


def ensure_ml_models_layout() -> None:
    ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    legacy_root = BASE_DIR / "backend"
    legacy_names = sorted({path.name for path in get_required_model_paths()})

    for name in legacy_names:
        target = ML_MODELS_DIR / name
        if target.exists():
            continue

        candidates = [
            BASE_DIR / name,
            legacy_root / name,
        ]
        source = next((candidate for candidate in candidates if candidate.exists()), None)
        if source is None:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
