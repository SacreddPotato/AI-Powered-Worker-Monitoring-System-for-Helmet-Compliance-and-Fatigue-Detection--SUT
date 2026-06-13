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
import os
import threading
import time

import cv2
from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger(__name__)

STREAM_FPS = max(8, int(os.environ.get("CAMERA_STREAM_FPS", "16")))
STREAM_FRAME_DELAY = 1.0 / STREAM_FPS
STREAM_JPEG_QUALITY = min(95, max(40, int(os.environ.get("CAMERA_STREAM_JPEG_QUALITY", "65"))))
INFERENCE_INTERVAL_MS = max(80, int(os.environ.get("CAMERA_INFERENCE_INTERVAL_MS", "260")))
COUNTING_INTERVAL_MS = max(120, int(os.environ.get("CAMERA_COUNTING_INTERVAL_MS", "300")))

# Reconnect backoff bounds.  The stream supervisor retries forever (capped delay)
# so a camera that drops mid-session always recovers on its own — the user never
# has to re-add the URL.
RECONNECT_BACKOFF_MIN_SECONDS = max(0.1, float(os.environ.get("CAMERA_RECONNECT_BACKOFF_MIN_SECONDS", "0.5")))
RECONNECT_BACKOFF_MAX_SECONDS = max(
    RECONNECT_BACKOFF_MIN_SECONDS,
    float(os.environ.get("CAMERA_RECONNECT_BACKOFF_MAX_SECONDS", "5")),
)
# Consecutive failed reads before treating the connection as dropped and reopening.
MAX_CONSECUTIVE_READ_FAILURES = max(5, int(os.environ.get("CAMERA_MAX_READ_FAILURES", "15")))


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
        """Supervise the camera stream, reconnecting indefinitely.

        A connection that drops mid-session no longer exhausts a fixed retry
        budget: any session that delivers at least one frame resets the backoff,
        and the supervisor keeps retrying (with a capped exponential delay,
        emitting the "No Signal" placeholder in between) until the client
        disconnects or the camera is removed/deactivated.  This is what lets a
        timed-out feed recover on its own instead of needing the URL re-added.
        """
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
        counting_updater = self._make_counting_updater()
        no_signal = _no_signal_frame()
        _, no_signal_jpg = cv2.imencode('.jpg', no_signal)
        no_signal_bytes = no_signal_jpg.tobytes()

        backoff = RECONNECT_BACKOFF_MIN_SECONDS
        while self._running:
            if not self._camera_active():
                logger.info("Camera %s: stream stopped because camera was removed or deactivated", self.camera_id)
                self._running = False
                break

            capture = _open_capture(source)
            if capture is None:
                logger.warning("Camera %s: open failed, retrying in %.1fs", source, backoff)
                if not self._safe_send_bytes(no_signal_bytes):
                    return  # client disconnected
                if not self._sleep_while_running(backoff):
                    return
                backoff = min(backoff * 2, RECONNECT_BACKOFF_MAX_SECONDS)
                continue

            delivered = self._run_session(capture, source, annotator, counting_updater)
            if not self._running:
                return

            if delivered:
                # The connection was healthy for a while; start fresh next time.
                backoff = RECONNECT_BACKOFF_MIN_SECONDS
            else:
                backoff = min(backoff * 2, RECONNECT_BACKOFF_MAX_SECONDS)

            if self._camera_active():
                logger.info("Camera %s: reconnecting in %.1fs", source, backoff)
                if not self._safe_send_bytes(no_signal_bytes):
                    return
                if not self._sleep_while_running(backoff):
                    return

    def _run_session(self, capture, source, annotator, counting_updater):
        """Read and stream frames from an open capture until it drops.

        Returns True if at least one frame was delivered (a healthy session)."""
        delivered = False
        consecutive_failures = 0
        try:
            while self._running:
                if not self._camera_active():
                    logger.info("Camera %s: stream stopped because camera was removed or deactivated", self.camera_id)
                    self._running = False
                    return delivered

                ok, frame = capture.read()
                if not ok:
                    consecutive_failures += 1
                    if consecutive_failures > MAX_CONSECUTIVE_READ_FAILURES:
                        logger.warning("Camera %s: lost too many frames, reconnecting", source)
                        return delivered
                    time.sleep(0.03)
                    continue
                consecutive_failures = 0

                raw_frame = frame
                # Always run annotator if available. Overlay selection is handled inside draw_annotations.
                if annotator is not None:
                    try:
                        frame = annotator(frame)
                    except Exception:
                        logger.exception("Annotation error on camera %s", self.camera_id)

                # Counting zones are drawn on every frame so the box stays visible
                # at all times, independent of which PPE overlays are enabled.
                try:
                    frame = counting_updater(raw_frame, frame)
                except Exception:
                    logger.exception("Counting error on camera %s", self.camera_id)

                _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, STREAM_JPEG_QUALITY])
                if jpeg is None:
                    continue
                if not self._safe_send_bytes(jpeg.tobytes()):
                    self._running = False
                    return delivered  # client disconnected
                delivered = True

                # Throttle to a stable FPS so encode/send does not overwhelm the event loop.
                time.sleep(STREAM_FRAME_DELAY)
        finally:
            capture.release()
        return delivered

    def _camera_active(self):
        from .models import Camera
        return Camera.objects.filter(pk=self.camera_id, is_active=True).exists()

    def _sleep_while_running(self, seconds):
        """Sleep in small slices, returning False as soon as the stream stops."""
        deadline = time.monotonic() + seconds
        while self._running and time.monotonic() < deadline:
            time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))
        return self._running

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

    def _make_counting_updater(self):
        """Build the closure that draws counting zones every frame and runs
        person detection on a throttled cadence in the background.

        Returns ``updater(raw_frame, output_frame) -> output_frame``.  The zone
        boxes + counts are drawn on every frame from the latest persisted state so
        they are always visible; the heavier person-detection + entry-counting work
        runs off-thread so it never stalls frame delivery.
        """
        from . import counting
        from annotation import draw_counting_zones

        state_lock = threading.Lock()
        inflight = {"value": False}
        last_ts = {"value": 0.0}
        interval_seconds = COUNTING_INTERVAL_MS / 1000.0

        def run_cycle(raw_snapshot):
            try:
                from detection.services import detect_people

                height, width = raw_snapshot.shape[:2]
                boxes = detect_people(raw_snapshot)
                counting.update(self.camera_id, boxes, width, height)
            except Exception:
                logger.exception("Counting cycle error on camera %s", self.camera_id)
            finally:
                with state_lock:
                    inflight["value"] = False

        def updater(raw_frame, output_frame):
            zones = counting.snapshot(self.camera_id)
            if not zones:
                return output_frame

            now = time.monotonic()
            should_launch = False
            with state_lock:
                if (now - last_ts["value"]) >= interval_seconds and not inflight["value"]:
                    inflight["value"] = True
                    last_ts["value"] = now
                    should_launch = True

            if should_launch:
                threading.Thread(
                    target=run_cycle, args=(raw_frame.copy(),), daemon=True
                ).start()

            return draw_counting_zones(output_frame, zones)

        return updater

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
        state_lock = threading.Lock()
        inference_inflight = {"value": False}
        last_inference_ts = {"value": 0.0}
        heartbeat_counter = {"value": 0}
        inference_interval_seconds = INFERENCE_INTERVAL_MS / 1000.0
        LOG_EVERY_N_INFERENCE_CYCLES = 12

        def run_inference_cycle(frame_snapshot):
            try:
                if not svc.ready:
                    mark_loading(self.camera_id)
                    return

                enabled = get_effective_enabled_model_keys(self.camera_id)
                if not enabled:
                    with state_lock:
                        cached.clear()
                        last_inference_ts["value"] = time.monotonic()
                    mark_disabled(self.camera_id)
                    return

                new = {}
                for key in enabled:
                    new[key] = svc.run_inference_on_frame(key, frame_snapshot, camera_id=self.camera_id)

                if camera is not None:
                    for key, result in new.items():
                        create_alert_from_inference(camera=camera, model_key=key, result=result)

                detected_count = sum(1 for item in new.values() if bool(item.get("detected")))
                with state_lock:
                    cached.clear()
                    cached.update(new)
                    heartbeat_counter["value"] += 1
                    last_inference_ts["value"] = time.monotonic()

                mark_running(self.camera_id, model_keys=enabled, detected_count=detected_count)

                if heartbeat_counter["value"] % LOG_EVERY_N_INFERENCE_CYCLES == 0:
                    logger.info(
                        "Inference heartbeat camera=%s models=%s detections=%s overlays=%s interval_ms=%s",
                        self.camera_id,
                        sorted(enabled),
                        detected_count,
                        sorted(self._overlays) if self._overlays else "all",
                        INFERENCE_INTERVAL_MS,
                    )
            except Exception:
                mark_error(self.camera_id, "inference_exception")
                logger.exception("Inference exception on camera %s", self.camera_id)
            finally:
                with state_lock:
                    inference_inflight["value"] = False

        def annotate(frame):
            if not svc.ready:
                mark_loading(self.camera_id)
                return frame

            now = time.monotonic()
            should_launch = False
            with state_lock:
                import config as cfg
                low_latency_mode = bool(getattr(cfg, "LOW_LATENCY_MODE", True))
                due = (
                    (now - last_inference_ts["value"]) >= inference_interval_seconds
                    if low_latency_mode
                    else True
                )
                if due and not inference_inflight["value"]:
                    inference_inflight["value"] = True
                    should_launch = True

            if should_launch:
                threading.Thread(
                    target=run_inference_cycle,
                    args=(frame.copy(),),
                    daemon=True,
                ).start()

            with state_lock:
                cached_snapshot = dict(cached)

            if not cached_snapshot:
                return frame

            try:
                return draw_annotations(frame, cached_snapshot, enabled_overlays=self._overlays)
            except Exception:
                mark_error(self.camera_id, "annotation_exception")
                logger.exception("Annotation exception on camera %s", self.camera_id)
                return frame

        return annotate
