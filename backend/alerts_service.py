import json
from typing import Callable, Dict, List, Optional


class AlertsService:
    def __init__(self, conn_factory: Callable):
        self._conn_factory = conn_factory

    def _severity_for_model(self, model_key: str) -> str:
        if model_key in {"helmet", "fatigue"}:
            return "high"
        if model_key == "vest":
            return "medium"
        return "low"

    def _build_message(self, model_name: str, camera_id: int, payload: Dict) -> str:
        vest_id = payload.get("vest_id") if isinstance(payload, dict) else None
        if vest_id:
            return f"{model_name} detected on camera {camera_id}. Vest ID: {vest_id}"
        if isinstance(payload, dict) and payload.get("trigger_reason"):
            reasons = payload.get("trigger_reason", [])
            if "head_tilt" in reasons:
                tilt = payload.get("head_tilt_degrees")
                return f"{model_name} head tilt alert on camera {camera_id} ({tilt}°)"
            if "sustained_fatigue" in reasons:
                frames = payload.get("consecutive_fatigue_frames")
                return f"{model_name} sustained fatigue alert on camera {camera_id} ({frames} frames)"
        if isinstance(payload, dict) and payload.get("classification") == "helmet_missing":
            missing = payload.get("no_helmet_count", 1)
            return f"{model_name} detected {missing} worker(s) without helmet on camera {camera_id}"
        return f"{model_name} detected on camera {camera_id}"

    def record_detections(
        self, camera_id: int, detections: List[Dict], threshold: float
    ) -> Dict[str, List[Dict]]:
        saved_detections: List[Dict] = []
        created_alerts: List[Dict] = []

        with self._conn_factory() as conn:
            for detection in detections:
                payload = detection.get("payload", {})
                cursor = conn.execute(
                    """
                    INSERT INTO detections (camera_id, model_key, status, detected, confidence, payload)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        camera_id,
                        detection["model_key"],
                        detection["status"],
                        int(bool(detection["detected"])),
                        float(detection["confidence"]),
                        json.dumps(payload),
                    ),
                )
                detection_id = cursor.lastrowid
                saved_detections.append(
                    {
                        "id": detection_id,
                        "camera_id": camera_id,
                        "model_key": detection["model_key"],
                        "model_name": detection["model_name"],
                        "status": detection["status"],
                        "detected": bool(detection["detected"]),
                        "confidence": float(detection["confidence"]),
                        "payload": payload,
                    }
                )

                should_alert = (
                    detection["status"] == "ok"
                    and bool(detection["detected"])
                    and float(detection["confidence"]) >= threshold
                )
                if not should_alert:
                    continue

                severity = self._severity_for_model(detection["model_key"])
                message = self._build_message(
                    detection["model_name"], camera_id, payload
                )
                alert_cursor = conn.execute(
                    """
                    INSERT INTO alerts (detection_id, camera_id, model_key, severity, message)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (detection_id, camera_id, detection["model_key"], severity, message),
                )
                created_alerts.append(
                    {
                        "id": alert_cursor.lastrowid,
                        "detection_id": detection_id,
                        "camera_id": camera_id,
                        "model_key": detection["model_key"],
                        "severity": severity,
                        "message": message,
                        "status": "open",
                    }
                )

        return {"detections": saved_detections, "alerts": created_alerts}

    def list_alerts(
        self,
        status: Optional[str] = None,
        camera_id: Optional[int] = None,
        model_key: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        where = []
        params: List = []
        if status:
            where.append("status = ?")
            params.append(status)
        if camera_id is not None:
            where.append("camera_id = ?")
            params.append(camera_id)
        if model_key:
            where.append("model_key = ?")
            params.append(model_key)

        query = "SELECT * FROM alerts"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY datetime(created_at) DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))

        with self._conn_factory() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def acknowledge_alert(self, alert_id: int) -> bool:
        with self._conn_factory() as conn:
            cursor = conn.execute(
                """
                UPDATE alerts
                SET status = 'acknowledged', acknowledged_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (alert_id,),
            )
            return cursor.rowcount > 0

    def list_detections(
        self,
        camera_id: Optional[int] = None,
        model_key: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        where = []
        params: List = []
        if camera_id is not None:
            where.append("camera_id = ?")
            params.append(camera_id)
        if model_key:
            where.append("model_key = ?")
            params.append(model_key)

        query = "SELECT * FROM detections"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY datetime(created_at) DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))

        with self._conn_factory() as conn:
            rows = conn.execute(query, params).fetchall()
            detections = []
            for row in rows:
                item = dict(row)
                item["detected"] = bool(item["detected"])
                item["payload"] = json.loads(item["payload"]) if item["payload"] else {}
                detections.append(item)
            return detections
