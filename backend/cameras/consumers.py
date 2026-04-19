"""WebSocket consumer that streams camera frames as binary JPEG messages.

Production-grade alternative to MJPEG over StreamingHttpResponse which
does not work reliably through Daphne's ASGI handler.

Protocol
--------
Client sends JSON to configure the stream::

    {"overlays": ["helmet","fatigue","vest","gloves","goggles"]}

Server sends binary JPEG frames continuously until the client disconnects.
"""
import json
import logging
import threading
import time

import cv2
from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger(__name__)


class CameraStreamConsumer(WebsocketConsumer):
    """Stream camera frames over WebSocket as binary JPEG messages."""

    def connect(self):
        self.camera_id = int(self.scope["url_route"]["kwargs"]["camera_id"])
        self._running = False
        self._thread = None
        self._overlays = None  # None = all overlays; set() = specific models
        self.accept()
        from .inference_status import mark_loading
        mark_loading(self.camera_id)
        # Start streaming immediately
        self._start_stream()

    def disconnect(self, close_code):
        self._running = False
        from .inference_status import mark_stream_stopped
        mark_stream_stopped(self.camera_id)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def receive(self, text_data=None, bytes_data=None):
        """Handle overlay configuration messages from the client."""
        if not text_data:
            return
        try:
            msg = json.loads(text_data)
            if "overlays" in msg:
                overlays = msg["overlays"]
                self._overlays = set(overlays) if overlays else None
                logger.info("Camera %s: overlays set to %s", self.camera_id, self._overlays)
        except (json.JSONDecodeError, TypeError):
            pass

    def _start_stream(self):
        self._running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()

    def _stream_loop(self):
        from .services import _open_capture, _no_signal_frame, _to_capture_source
        from .models import Camera

        try:
            camera = Camera.objects.get(pk=self.camera_id)
        except Camera.DoesNotExist:
            logger.error("Camera %s does not exist", self.camera_id)
            self._send_no_signal()
            return

        source = _to_capture_source(camera.source_url)
        annotator = self._make_annotator()
        no_signal = _no_signal_frame()
        _, no_signal_jpg = cv2.imencode('.jpg', no_signal)
        no_signal_bytes = no_signal_jpg.tobytes()

        max_retries = 3
        for attempt in range(max_retries):
            if not self._running:
                return

            capture = _open_capture(source)
            if capture is None:
                logger.warning("Camera %s: open failed (attempt %d/%d)", source, attempt + 1, max_retries)
                self._safe_send_bytes(no_signal_bytes)
                time.sleep(1)
                continue

            consecutive_failures = 0
            try:
                while self._running:
                    if not Camera.objects.filter(pk=self.camera_id, is_active=True).exists():
                        logger.info("Camera %s: stream stopped because camera was removed or deactivated", self.camera_id)
                        self._running = False
                        return

                    ok, frame = capture.read()
                    if not ok:
                        consecutive_failures += 1
                        if consecutive_failures > 15:
                            logger.warning("Camera %s: lost too many frames, reconnecting", source)
                            break
                        time.sleep(0.03)
                        continue
                    consecutive_failures = 0

                    # Always run annotator if available. Overlay selection is handled inside draw_annotations.
                    if annotator is not None:
                        try:
                            frame = annotator(frame)
                        except Exception:
                            logger.exception("Annotation error on camera %s", self.camera_id)

                    _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if jpeg is None:
                        continue
                    if not self._safe_send_bytes(jpeg.tobytes()):
                        return  # client disconnected

                    # Throttle to ~25 FPS to avoid overwhelming the WS
                    time.sleep(0.04)
            finally:
                capture.release()

        # Exhausted retries
        if self._running:
            logger.error("Camera %s: giving up after %d attempts", source, max_retries)
            self._safe_send_bytes(no_signal_bytes)

    def _safe_send_bytes(self, data):
        """Send binary data, return False if the socket is closed."""
        try:
            self.send(bytes_data=data)
            return True
        except Exception:
            self._running = False
            return False

    def _send_no_signal(self):
        from .services import _no_signal_frame
        frame = _no_signal_frame()
        _, jpg = cv2.imencode('.jpg', frame)
        self._safe_send_bytes(jpg.tobytes())

    def _make_annotator(self):
        """Build the annotation closure (same logic as views._make_annotator
        but driven by self._overlays which can change at runtime)."""
        from detection.services import get_inference_service, get_effective_enabled_model_keys
        from alerts.services import create_alert_from_inference
        from annotation import draw_annotations
        from .models import Camera
        from .inference_status import mark_loading, mark_disabled, mark_running, mark_error

        svc = get_inference_service()
        camera = Camera.objects.filter(pk=self.camera_id).first()
        if not svc.ready:
            threading.Thread(target=svc.preload, daemon=True).start()

        cached = {}
        counter = [0]
        INFERENCE_INTERVAL = 5
        heartbeat_counter = [0]
        LOG_EVERY_N_INFERENCE_CYCLES = 12

        def annotate(frame):
            if not svc.ready:
                mark_loading(self.camera_id)
                return frame
            counter[0] += 1
            try:
                if counter[0] % INFERENCE_INTERVAL == 1 or not cached:
                    enabled = get_effective_enabled_model_keys(self.camera_id)
                    if not enabled:
                        cached.clear()
                        mark_disabled(self.camera_id)
                        return frame
                    new = {}
                    for key in enabled:
                        new[key] = svc.run_inference_on_frame(key, frame, camera_id=self.camera_id)
                    if camera is not None:
                        for key, result in new.items():
                            create_alert_from_inference(camera=camera, model_key=key, result=result)
                    detected_count = sum(1 for item in new.values() if bool(item.get("detected")))
                    mark_running(self.camera_id, model_keys=enabled, detected_count=detected_count)
                    heartbeat_counter[0] += 1
                    if heartbeat_counter[0] % LOG_EVERY_N_INFERENCE_CYCLES == 0:
                        logger.info(
                            "Inference heartbeat camera=%s models=%s detections=%s overlays=%s",
                            self.camera_id,
                            sorted(enabled),
                            detected_count,
                            sorted(self._overlays) if self._overlays else "all",
                        )
                    cached.clear()
                    cached.update(new)
                return draw_annotations(frame, cached, enabled_overlays=self._overlays)
            except Exception:
                mark_error(self.camera_id, "inference_exception")
                logger.exception("Inference exception on camera %s", self.camera_id)
                return frame

        return annotate
