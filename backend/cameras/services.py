"""Wraps existing camera_service.py for Django views."""
import logging
import sys
import time

import cv2
import numpy as np
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_IS_WINDOWS = sys.platform == "win32"

# Backends to try, in order.  DirectShow is far more reliable on Windows for
# sustained streaming; the default MSMF backend often hangs after the first
# frame when the device is re-opened quickly.
_BACKENDS = (
    [cv2.CAP_DSHOW, cv2.CAP_ANY] if _IS_WINDOWS else [cv2.CAP_ANY]
)

_MAX_RETRIES = 3
_RETRY_DELAY = 0.5  # seconds


def _to_capture_source(source_url: str):
    return int(source_url) if str(source_url).isdigit() else source_url


def _open_capture(source):
    """Try each backend in order and return the first that works.
    Catches C++ exceptions from OpenCV that would otherwise crash the process."""
    backends = _BACKENDS if isinstance(source, int) else [cv2.CAP_ANY]
    for backend in backends:
        try:
            cap = cv2.VideoCapture(source, backend)
            if not cap.isOpened():
                cap.release()
                continue
            # Network streams can be slow to deliver the first frame
            if isinstance(source, str) and not source.isdigit():
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            ok, _ = cap.read()
            if ok:
                logger.info("Camera %s opened with backend %s", source, backend)
                return cap
            cap.release()
        except Exception:
            logger.exception("OpenCV error opening %s with backend %s", source, backend)
    return None


def _no_signal_frame(width=640, height=480):
    """Generate a dark placeholder frame with a 'No Signal' message."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = (18, 18, 22)  # dark background matching UI
    text = "No Signal"
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(text, font, 0.9, 2)
    x = (width - tw) // 2
    y = (height + th) // 2
    cv2.putText(frame, text, (x, y), font, 0.9, (80, 80, 100), 2, cv2.LINE_AA)
    # Camera icon (simple circle + rectangle)
    cx, cy = width // 2, height // 2 - 40
    cv2.rectangle(frame, (cx - 24, cy - 16), (cx + 24, cy + 16), (60, 60, 80), 2)
    cv2.circle(frame, (cx, cy), 8, (60, 60, 80), 2)
    return frame


class DjangoCameraService:
    """Thin adapter that provides camera operations without the legacy
    sqlite conn_factory, since Django models handle persistence."""

    def check_camera_status(self, source_url):
        source = _to_capture_source(source_url)
        cap = _open_capture(source)
        connected = cap is not None
        if cap:
            cap.release()

        return {
            'connected': connected,
            'frame_read': connected,
            'source_url': source_url,
            'checked_at': datetime.now(timezone.utc).isoformat(),
        }

    def stream_frames(self, source_url, camera_id=None, annotate_fn=None):
        """Yield JPEG-encoded frames.  If annotate_fn is provided, each raw
        numpy frame is passed through it before encoding.

        Retries up to _MAX_RETRIES times if the camera connection drops.
        Yields a 'No Signal' placeholder while reconnecting so the MJPEG
        stream never goes blank."""
        source = _to_capture_source(source_url)
        no_signal = _no_signal_frame()
        _, placeholder_jpg = cv2.imencode('.jpg', no_signal)
        placeholder = placeholder_jpg.tobytes()

        retries = 0
        while retries < _MAX_RETRIES:
            capture = _open_capture(source)
            if capture is None:
                logger.warning(
                    "Camera %s: failed to open (attempt %d/%d)",
                    source, retries + 1, _MAX_RETRIES,
                )
                # Yield placeholder so the stream isn't blank
                yield placeholder
                retries += 1
                time.sleep(_RETRY_DELAY)
                continue

            # Successful connection — reset retries
            retries = 0
            consecutive_failures = 0
            try:
                while True:
                    ok, frame = capture.read()
                    if not ok:
                        consecutive_failures += 1
                        if consecutive_failures > 10:
                            logger.warning("Camera %s: lost %d frames, reconnecting", source, consecutive_failures)
                            break
                        yield placeholder
                        time.sleep(0.03)
                        continue
                    consecutive_failures = 0

                    if annotate_fn:
                        try:
                            frame = annotate_fn(frame)
                        except Exception:
                            logger.exception("Annotation error on camera %s", source)

                    _, jpeg = cv2.imencode('.jpg', frame)
                    if jpeg is None:
                        yield placeholder
                        continue
                    yield jpeg.tobytes()
            finally:
                capture.release()

            # If we broke out of the inner loop, try reconnecting
            retries += 1
            if retries < _MAX_RETRIES:
                logger.info("Camera %s: reconnecting (attempt %d/%d)", source, retries + 1, _MAX_RETRIES)
                time.sleep(_RETRY_DELAY)

        # Exhausted retries — yield a few more placeholders then exit
        logger.error("Camera %s: giving up after %d reconnect attempts", source, _MAX_RETRIES)
        for _ in range(30):  # ~1 second of placeholder frames
            yield placeholder
            time.sleep(0.033)

    @staticmethod
    def discover_devices(max_index=10):
        """Probe system video device indices and return available ones."""
        devices = []
        for i in range(max_index):
            cap = _open_capture(i)
            if cap is not None:
                # _open_capture already verified read() works; grab dimensions
                ok, frame = cap.read()
                if ok:
                    h, w = frame.shape[:2]
                else:
                    h, w = 480, 640
                devices.append({'index': i, 'name': f'Camera {i}', 'width': w, 'height': h})
                cap.release()
        return devices


_service = DjangoCameraService()


def get_camera_service():
    return _service
