import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
DATABASE_PATH = BASE_DIR / "monitoring.db"
UPLOADS_DIR = BASE_DIR / "uploads"
DEV_VIDEO_DIR = UPLOADS_DIR / "dev_videos"
ML_MODELS_DIR = BASE_DIR / "ml_models"

HELMET_MODEL_URL = os.environ.get(
    "HELMET_MODEL_URL",
    "https://huggingface.co/keremberke/yolov8n-hard-hat-detection/resolve/main/best.pt",
)
PPE_MULTI_MODEL_URL = os.environ.get(
    "PPE_MULTI_MODEL_URL",
    "https://huggingface.co/Tanishjain9/yolov8n-ppe-detection-6classes/resolve/main/best.pt",
)
PERSON_MODEL_URL = os.environ.get(
    "PERSON_MODEL_URL",
    "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt",
)
SHAPE_PREDICTOR_URL = os.environ.get(
    "SHAPE_PREDICTOR_URL",
    "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2",
)
BOOTS_MODEL_URL = os.environ.get(
    "BOOTS_MODEL_URL",
    "https://huggingface.co/keremberke/yolov8n-boots-detection/resolve/main/best.pt",
)
FACESHIELD_MODEL_URL = os.environ.get("FACESHIELD_MODEL_URL", "")
SAFETY_SUIT_MODEL_URL = os.environ.get("SAFETY_SUIT_MODEL_URL", "")

MODEL_DEFINITIONS = {
    "helmet": {
        "display_name": "Helmet Detection",
        "description": "Detects workers missing helmets using helmet + upper-body detection.",
        "weights_path": str(ML_MODELS_DIR / "best.pt"),
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "download_urls": [HELMET_MODEL_URL, PPE_MULTI_MODEL_URL],
        "person_download_urls": [PERSON_MODEL_URL],
        "target_labels": ["no-hardhat", "no_helmet", "no-helmet", "no hardhat"],
        "strict_target_match": False,
    },
    "fatigue": {
        "display_name": "Fatigue Detection",
        "description": "Hybrid fatigue scoring with Swin model + EAR/MAR + head tilt alerts.",
        "weights_path": str(ML_MODELS_DIR / "swin_best.pth"),
        "shape_predictor_path": str(ML_MODELS_DIR / "shape_predictor_68_face_landmarks.dat"),
        "download_urls": [],
        "shape_download_urls": [SHAPE_PREDICTOR_URL],
    },
    "vest": {
        "display_name": "Vest Detection",
        "description": "Detects high-visibility safety vests and reads vest QR IDs.",
        "weights_path": str(ML_MODELS_DIR / "vest_detection.pt"),
        "download_urls": [PPE_MULTI_MODEL_URL],
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "person_download_urls": [PERSON_MODEL_URL],
        "target_labels": ["vest", "safety vest", "safety_vest", "safety-vest"],
    },
    "gloves": {
        "display_name": "Gloves Detection",
        "description": "Detects worker safety gloves.",
        "weights_path": str(ML_MODELS_DIR / "gloves_detection.pt"),
        "download_urls": [],
        "target_labels": ["glove", "gloves", "no_glove", "no-glove"],
    },
    "goggles": {
        "display_name": "Goggles Detection",
        "description": "Detects protective eyewear (goggles).",
        "weights_path": str(ML_MODELS_DIR / "goggles_detection.pt"),
        "download_urls": [],
        "target_labels": ["goggles", "goggle", "no_goggles", "no-goggles"],
    },
    "boots": {
        "display_name": "Boot Detection",
        "description": "Detects worker safety boots.",
        "weights_path": str(ML_MODELS_DIR / "boots_detection.pt"),
        "download_urls": [BOOTS_MODEL_URL],
        "target_labels": ["boot", "boots", "safety boot", "safety boots", "no_boot", "no-boots", "no boots"],
        "strict_target_match": False,
    },
    "faceshield": {
        "display_name": "Face Shield Detection",
        "description": "Detects protective face shields.",
        "weights_path": str(ML_MODELS_DIR / "faceshield_detection.pt"),
        "download_urls": [FACESHIELD_MODEL_URL],
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "person_download_urls": [PERSON_MODEL_URL],
        "target_labels": ["face shield", "faceshield", "shield", "no_face_shield", "no-faceshield", "no shield"],
        "strict_target_match": False,
    },
    "safetysuit": {
        "display_name": "Safety Suit Detection",
        "description": "Detects protective safety suits/coveralls.",
        "weights_path": str(ML_MODELS_DIR / "safety_suit_detection.pt"),
        "download_urls": [SAFETY_SUIT_MODEL_URL],
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "person_download_urls": [PERSON_MODEL_URL],
        "target_labels": ["safety suit", "safetysuit", "coverall", "protective suit", "no_safety_suit", "no safety suit"],
        "strict_target_match": False,
    },
}

DEFAULT_ALERT_CONFIDENCE_THRESHOLD = 0.45
FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD = 8
HEAD_TILT_ALERT_DEGREES = 15.0


def ensure_ml_models_layout() -> None:
    ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    legacy_root = BASE_DIR / "backend"
    legacy_names = [
        "best.pt",
        "yolov8n.pt",
        "swin_best.pth",
        "shape_predictor_68_face_landmarks.dat",
        "vest_detection.pt",
        "gloves_detection.pt",
        "goggles_detection.pt",
        "boots_detection.pt",
        "faceshield_detection.pt",
        "safety_suit_detection.pt",
    ]

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
