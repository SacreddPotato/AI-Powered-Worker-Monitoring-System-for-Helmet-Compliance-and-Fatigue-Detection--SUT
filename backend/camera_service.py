from datetime import datetime, timezone
from typing import Callable, Dict, Generator, Optional

import cv2


def _to_capture_source(source_url: str):
    return int(source_url) if str(source_url).isdigit() else source_url


class CameraService:
    def __init__(self, conn_factory: Callable, model_keys):
        self._conn_factory = conn_factory
        self._model_keys = list(model_keys)

    def _row_to_dict(self, row) -> Dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "source_url": row["source_url"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_cameras(self):
        with self._conn_factory() as conn:
            rows = conn.execute(
                "SELECT * FROM cameras ORDER BY id ASC"
            ).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_camera(self, camera_id: int) -> Optional[Dict]:
        with self._conn_factory() as conn:
            row = conn.execute(
                "SELECT * FROM cameras WHERE id = ?", (camera_id,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)

    def create_camera(self, name: str, source_url: str, is_active: bool = True) -> Dict:
        with self._conn_factory() as conn:
            cursor = conn.execute(
                """
                INSERT INTO cameras (name, source_url, is_active)
                VALUES (?, ?, ?)
                """,
                (name, source_url, int(is_active)),
            )
            camera_id = cursor.lastrowid
            for model_key in self._model_keys:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO camera_models (camera_id, model_key, enabled)
                    VALUES (?, ?, 1)
                    """,
                    (camera_id, model_key),
                )
        return self.get_camera(camera_id)

    def update_camera(self, camera_id: int, payload: Dict) -> Optional[Dict]:
        camera = self.get_camera(camera_id)
        if camera is None:
            return None

        name = payload.get("name", camera["name"])
        source_url = payload.get("source_url", camera["source_url"])
        is_active = payload.get("is_active", camera["is_active"])
        is_active = bool(is_active)

        with self._conn_factory() as conn:
            conn.execute(
                """
                UPDATE cameras
                SET name = ?, source_url = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, source_url, int(is_active), camera_id),
            )
        return self.get_camera(camera_id)

    def delete_camera(self, camera_id: int) -> bool:
        with self._conn_factory() as conn:
            cursor = conn.execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
            return cursor.rowcount > 0

    def get_camera_status(self, camera_id: int) -> Optional[Dict]:
        camera = self.get_camera(camera_id)
        if camera is None:
            return None

        source = _to_capture_source(camera["source_url"])
        capture = cv2.VideoCapture(source)
        connected = capture.isOpened()
        frame_read = False
        if connected:
            frame_read, _ = capture.read()
            connected = bool(frame_read)
        capture.release()

        return {
            "camera_id": camera_id,
            "connected": connected,
            "frame_read": frame_read,
            "source_url": camera["source_url"],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_single_frame(self, camera_id: int):
        camera = self.get_camera(camera_id)
        if camera is None:
            return None, "Camera not found"

        source = _to_capture_source(camera["source_url"])
        capture = cv2.VideoCapture(source)
        if not capture.isOpened():
            capture.release()
            return None, "Unable to connect to camera source"

        ok, frame = capture.read()
        capture.release()
        if not ok:
            return None, "Unable to read a frame from camera"

        return frame, None

    def stream_frames(self, camera_id: int) -> Generator[bytes, None, None]:
        camera = self.get_camera(camera_id)
        if camera is None:
            return

        source = _to_capture_source(camera["source_url"])
        yield from self.stream_source(source)

    def stream_source(self, source_url) -> Generator[bytes, None, None]:
        source = _to_capture_source(source_url)
        capture = cv2.VideoCapture(source)

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                encoded, jpeg = cv2.imencode(".jpg", frame)
                if not encoded:
                    continue

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
                )
        finally:
            capture.release()
