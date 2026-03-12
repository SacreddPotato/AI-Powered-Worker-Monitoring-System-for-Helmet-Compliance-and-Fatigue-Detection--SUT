"""Wraps existing inference_service.py and model_service.py."""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import MODEL_DEFINITIONS

_inference_service = None


class _DjangoInferenceAdapter:
    """Lazy wrapper around InferenceService that defers heavy model loading
    until the first actual inference call."""

    def __init__(self):
        self._real = None

    def _ensure_loaded(self):
        if self._real is None:
            from inference_service import InferenceService as _IS
            self._real = _IS(MODEL_DEFINITIONS)

    def get_model_health(self, model_key):
        self._ensure_loaded()
        return self._real.get_model_health(model_key)

    def run_inference(self, model_key, source_url, camera_id=0):
        """Run inference by grabbing a frame from the source_url."""
        self._ensure_loaded()
        import cv2
        cap = cv2.VideoCapture(
            int(source_url) if str(source_url).isdigit() else source_url
        )
        ok, frame = cap.read()
        cap.release()
        if not ok:
            return {
                'status': 'error',
                'detected': False,
                'confidence': 0.0,
                'payload': {'error': 'Could not read frame from source'},
            }
        results = self._real.run_models(frame, [model_key], camera_id=camera_id)
        return results[0] if results else {
            'status': 'error',
            'detected': False,
            'confidence': 0.0,
            'payload': {'error': 'No result returned'},
        }

    def run_inference_on_frame(self, model_key, frame, camera_id=0):
        """Run inference directly on a provided frame (for devlab)."""
        self._ensure_loaded()
        results = self._real.run_models(frame, [model_key], camera_id=camera_id)
        return results[0] if results else {
            'status': 'error',
            'detected': False,
            'confidence': 0.0,
            'payload': {'error': 'No result returned'},
        }


def get_inference_service():
    global _inference_service
    if _inference_service is None:
        _inference_service = _DjangoInferenceAdapter()
    return _inference_service


def get_model_definitions():
    return MODEL_DEFINITIONS
