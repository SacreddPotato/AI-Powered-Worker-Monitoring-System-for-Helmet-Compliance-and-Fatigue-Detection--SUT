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

    def stream_frames(self, source_url, camera_id=None, annotate_fn=None):
        """Yield JPEG-encoded frames. If annotate_fn is provided, each raw
        numpy frame is passed through it before encoding."""
        source = _to_capture_source(source_url)
        capture = cv2.VideoCapture(source)
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if annotate_fn:
                    frame = annotate_fn(frame)
                _, jpeg = cv2.imencode('.jpg', frame)
                if jpeg is None:
                    continue
                yield jpeg.tobytes()
        finally:
            capture.release()

    @staticmethod
    def discover_devices(max_index=10):
        """Probe system video device indices and return available ones."""
        devices = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    h, w = frame.shape[:2]
                    devices.append({'index': i, 'name': f'Camera {i}', 'width': w, 'height': h})
                cap.release()
            else:
                cap.release()
        return devices


_service = DjangoCameraService()


def get_camera_service():
    return _service
