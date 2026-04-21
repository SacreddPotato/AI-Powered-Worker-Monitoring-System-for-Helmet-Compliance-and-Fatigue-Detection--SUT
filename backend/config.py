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

MODEL_DEFINITIONS = {
    "helmet": {
        "display_name": "Helmet Detection",
        "description": "Detects workers missing helmets using helmet + upper-body detection.",
        "weights_path": str(ML_MODELS_DIR / "best.pt"),
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "download_urls": [HELMET_MODEL_URL, PPE_MULTI_MODEL_URL],
        "person_download_urls": [PERSON_MODEL_URL],
        # Only presence classes. Absence is calculated via person box overlap.
        "target_labels": ["hardhat", "helmet", "safety helmet"],
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
        # Actual model classes: ['no vest', 'vest']
        "target_labels": ["vest", "no vest"],
        "strict_target_match": True,
        "conf_threshold": 0.40,
    },
    "gloves": {
        "display_name": "Gloves Detection",
        "description": "Detects worker safety gloves.",
        "weights_path": str(ML_MODELS_DIR / "gloves_detection.pt"),
        "download_urls": [],
        # Absence detection handled by MediaPipe hand regions
        "target_labels": ["glove", "gloves", "no glove", "no gloves", "no_glove", "no-glove"],
        "strict_target_match": False,
        "conf_threshold": 0.40,
    },
    "goggles": {
        "display_name": "Goggles Detection",
        "description": "Detects protective eyewear (goggles).",
        "weights_path": str(ML_MODELS_DIR / "goggles_detection.pt"),
        "download_urls": [],
        # Actual model classes: ['safety_goggles'] — presence only
        # Absence detection handled by MediaPipe eye-region tracking
        "target_labels": ["safety_goggles", "safety goggles", "goggles", "goggle"],
        "strict_target_match": False,
        "conf_threshold": 0.50,  # raised to reduce sunglasses false positives
    },
    "face_shield": {
        "display_name": "Face Shield Detection",
        "description": "Detects protective face shields in hazardous environments.",
        "weights_path": str(ML_MODELS_DIR / "face_shield_detection.pt"),
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "download_urls": [],
        "person_download_urls": [PERSON_MODEL_URL],
        # Actual model classes: ['.', 'Face Shield'] — '.' is a garbage class to ignore
        "target_labels": ["face shield", "face-shield"],
        "strict_target_match": False,
        "conf_threshold": 0.85,  # very high — real face shields are very distinct; 0.60 still fires on sunglasses at 76%
    },
    "safety_suit": {
        "display_name": "Safety Suit Detection",
        "description": "Ensures workers are wearing full-body safety suits.",
        "weights_path": str(ML_MODELS_DIR / "safety_suit_detection.pt"),
        "person_model_path": str(ML_MODELS_DIR / "yolov8n.pt"),
        "download_urls": [],
        "person_download_urls": [PERSON_MODEL_URL],
        # Actual model classes: ['safety_suit', 'safety_vest'] — presence only
        # No absence label exists in this model; detection means PRESENT (compliant)
        "target_labels": ["safety_suit", "safety suit", "safety_vest", "safety vest"],
        "strict_target_match": False,
        "conf_threshold": 0.75,  # aggressive — dark formal blazers still triggered at 0.55
    },
}

DEFAULT_ALERT_CONFIDENCE_THRESHOLD = 0.35
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
