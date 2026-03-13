import json
import threading
import cv2
from channels.generic.websocket import WebsocketConsumer
from .models import DevVideo
from detection.services import get_inference_service


class VideoAnalysisConsumer(WebsocketConsumer):
    """Stream per-frame analysis results over WebSocket as the video is processed."""

    def connect(self):
        self.accept()
        self._thread = None
        self._stop = threading.Event()
        # Kick off model preloading so inference is ready faster
        svc = get_inference_service()
        if not svc.ready:
            threading.Thread(target=svc.preload, daemon=True).start()

    def disconnect(self, close_code):
        self._stop.set()

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'start':
            # Stop any running analysis
            self._stop.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
            self._stop.clear()

            self._thread = threading.Thread(
                target=self._run,
                args=(data.get('video_id'), data.get('sample_every_n_frames', 3)),
                daemon=True,
            )
            self._thread.start()

        elif action == 'stop':
            self._stop.set()

    def _run(self, video_id, sample_every):
        try:
            video = DevVideo.objects.get(pk=video_id)
            svc = get_inference_service()
            svc.preload()

            cap = cv2.VideoCapture(video.file_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            from detection.models import ModelSetting
            enabled = list(
                ModelSetting.objects.filter(is_enabled=True).values_list('key', flat=True)
            )

            self._send({
                'type': 'init',
                'fps': round(fps, 2),
                'total_frames': total_frames,
                'enabled_models': enabled,
            })

            frame_idx = 0
            analyzed = 0

            while cap.isOpened() and not self._stop.is_set():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % sample_every == 0:
                    detections = {}
                    for key in enabled:
                        detections[key] = svc.run_inference_on_frame(key, frame, camera_id=0)

                    self._send({
                        'type': 'frame',
                        'frame': frame_idx,
                        'detections': detections,
                    })
                    analyzed += 1

                frame_idx += 1

            cap.release()

            if not self._stop.is_set():
                self._send({
                    'type': 'done',
                    'frames_total': frame_idx,
                    'frames_analyzed': analyzed,
                })

        except Exception as exc:
            self._send({'type': 'error', 'message': str(exc)})

    def _send(self, data):
        """Send JSON, silently stopping if the socket is gone."""
        try:
            self.send(text_data=json.dumps(data))
        except Exception:
            self._stop.set()
