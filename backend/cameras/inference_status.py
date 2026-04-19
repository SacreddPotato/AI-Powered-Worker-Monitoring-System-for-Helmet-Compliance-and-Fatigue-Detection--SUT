from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Iterable

_STATUS_BY_CAMERA: Dict[int, Dict[str, Any]] = {}
_LOCK = threading.Lock()


def _now_ts() -> float:
    return time.time()


def _iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _upsert(camera_id: int, status: str, *, model_keys: Iterable[str] | None = None, detected_count: int | None = None, error: str | None = None) -> None:
    now = _now_ts()
    payload = {
        "camera_id": int(camera_id),
        "status": status,
        "updated_ts": now,
    }
    if model_keys is not None:
        payload["model_keys"] = sorted(set(model_keys))
    if detected_count is not None:
        payload["detected_count"] = int(detected_count)
    if error:
        payload["last_error"] = str(error)

    if status == "running":
        payload["last_inference_ts"] = now

    with _LOCK:
        prev = _STATUS_BY_CAMERA.get(int(camera_id), {})
        merged = {**prev, **payload}
        _STATUS_BY_CAMERA[int(camera_id)] = merged


def mark_loading(camera_id: int) -> None:
    _upsert(camera_id, "loading")


def mark_disabled(camera_id: int, *, model_keys: Iterable[str] | None = None) -> None:
    _upsert(camera_id, "disabled", model_keys=model_keys, detected_count=0)


def mark_running(camera_id: int, *, model_keys: Iterable[str], detected_count: int) -> None:
    _upsert(camera_id, "running", model_keys=model_keys, detected_count=detected_count)


def mark_error(camera_id: int, error: str) -> None:
    _upsert(camera_id, "error", error=error)


def mark_stream_stopped(camera_id: int) -> None:
    _upsert(camera_id, "stopped")


def get_inference_status(camera_id: int, *, stale_after_seconds: int = 15) -> Dict[str, Any]:
    now = _now_ts()
    with _LOCK:
        raw = dict(_STATUS_BY_CAMERA.get(int(camera_id), {}))

    if not raw:
        return {
            "camera_id": int(camera_id),
            "status": "unknown",
            "is_stale": True,
            "age_seconds": None,
            "updated_at": None,
            "last_inference_at": None,
            "model_keys": [],
            "detected_count": 0,
            "last_error": None,
        }

    updated_ts = raw.get("updated_ts")
    last_inference_ts = raw.get("last_inference_ts")

    age_seconds = int(max(0, now - updated_ts)) if updated_ts is not None else None
    inference_age = int(max(0, now - last_inference_ts)) if last_inference_ts is not None else None

    status = raw.get("status", "unknown")
    is_stale = False
    if status == "running" and inference_age is not None and inference_age > stale_after_seconds:
        status = "stale"
        is_stale = True

    return {
        "camera_id": int(camera_id),
        "status": status,
        "is_stale": is_stale,
        "age_seconds": age_seconds,
        "inference_age_seconds": inference_age,
        "updated_at": _iso(updated_ts),
        "last_inference_at": _iso(last_inference_ts),
        "model_keys": raw.get("model_keys", []),
        "detected_count": int(raw.get("detected_count", 0) or 0),
        "last_error": raw.get("last_error"),
    }
