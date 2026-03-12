"""Wraps existing camera_service.py for Django views."""
import cv2
from datetime import datetime, timezone


def _to_capture_source(source_url: str):
    return int(source_url) if str(source_url).isdigit() else source_url


class DjangoCameraService:
    """Thin adapter that provides camera operations without the legacy
    sqlite conn_factory, since Django models handle persistence."""

    def check_camera_status(self, source_url):
        source = _to_capture_source(source_url)
        capture = cv2.VideoCapture(source)
        connected = capture.isOpened()
        frame_read = False
        if connected:
            frame_read, _ = capture.read()
            connected = bool(frame_read)
        capture.release()

        return {
            'connected': connected,
            'frame_read': frame_read,
            'source_url': source_url,
            'checked_at': datetime.now(timezone.utc).isoformat(),
        }

    def stream_frames(self, source_url, camera_id=None, annotated=False):
        source = _to_capture_source(source_url)
        capture = cv2.VideoCapture(source)
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                _, jpeg = cv2.imencode('.jpg', frame)
                if jpeg is None:
                    continue
                yield jpeg.tobytes()
        finally:
            capture.release()


_service = DjangoCameraService()


def get_camera_service():
    return _service
