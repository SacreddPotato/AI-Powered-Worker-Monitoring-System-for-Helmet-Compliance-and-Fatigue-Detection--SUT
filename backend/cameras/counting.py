"""Per-camera runtime that turns person detections into persisted zone counts.

The pure tracking / counting logic lives in :mod:`people_counting`; this module is
the stateful, Django-aware glue that the streaming consumer drives:

* ``snapshot(camera_id)`` returns the current zones + live counts for drawing on
  every frame (cheap; the zone definitions are cached and refreshed periodically).
* ``update(camera_id, person_boxes, width, height)`` advances the tracker on the
  throttled inference cadence, applies entry events to the running counts, and
  flushes increments back to the ``CountingZone`` rows so counts survive restarts.

State is in-memory and single-process (matching ``inference_status``); the DB row
is the durable record.  While a camera is streaming the in-memory count is
authoritative, so a reset performed through the API also clears it via
``reset_zone`` to keep the burned-in overlay in sync immediately.
"""
from __future__ import annotations

import threading
import time
from typing import Dict, List

from django.utils import timezone

from people_counting import CentroidTracker, ZoneCounter

ZONE_REFRESH_SECONDS = 2.0


class _CameraRuntime:
    def __init__(self) -> None:
        self.tracker = CentroidTracker()
        self.zone_counter = ZoneCounter()
        self.counts: Dict[int, int] = {}
        self.zone_defs: Dict[int, Dict] = {}
        self.last_refresh: float = 0.0
        self.lock = threading.Lock()


_RUNTIMES: Dict[int, _CameraRuntime] = {}
_GLOBAL_LOCK = threading.Lock()


def _get_runtime(camera_id: int) -> _CameraRuntime:
    with _GLOBAL_LOCK:
        runtime = _RUNTIMES.get(camera_id)
        if runtime is None:
            runtime = _CameraRuntime()
            _RUNTIMES[camera_id] = runtime
        return runtime


def _refresh_zone_defs(runtime: _CameraRuntime, camera_id: int, force: bool = False) -> None:
    """Reload zone *definitions* from the DB (throttled).  Caller holds runtime.lock."""
    now = time.monotonic()
    if not force and runtime.zone_defs and (now - runtime.last_refresh) < ZONE_REFRESH_SECONDS:
        return

    from .models import CountingZone

    rows = list(
        CountingZone.objects.filter(camera_id=camera_id).values(
            'id', 'name', 'x1', 'y1', 'x2', 'y2', 'count'
        )
    )
    runtime.last_refresh = now

    seen_ids = set()
    new_defs: Dict[int, Dict] = {}
    for row in rows:
        zone_id = row['id']
        seen_ids.add(zone_id)
        new_defs[zone_id] = {
            'id': zone_id,
            'name': row['name'],
            'x1': row['x1'],
            'y1': row['y1'],
            'x2': row['x2'],
            'y2': row['y2'],
        }
        # Seed the in-memory running count from the DB the first time we see a zone.
        if zone_id not in runtime.counts:
            runtime.counts[zone_id] = int(row['count'])

    # Forget zones that have been deleted.
    for zone_id in list(runtime.counts):
        if zone_id not in seen_ids:
            runtime.counts.pop(zone_id, None)
            runtime.zone_counter.forget(zone_id)

    runtime.zone_defs = new_defs


def _snapshot(runtime: _CameraRuntime) -> List[Dict]:
    out = []
    for zone_id, zone in sorted(runtime.zone_defs.items()):
        out.append(
            {
                'id': zone_id,
                'name': zone['name'],
                'x1': zone['x1'],
                'y1': zone['y1'],
                'x2': zone['x2'],
                'y2': zone['y2'],
                'count': int(runtime.counts.get(zone_id, 0)),
            }
        )
    return out


def has_zones(camera_id: int) -> bool:
    """Whether the camera currently has at least one counting zone (cached)."""
    runtime = _get_runtime(camera_id)
    with runtime.lock:
        _refresh_zone_defs(runtime, camera_id)
        return bool(runtime.zone_defs)


def snapshot(camera_id: int) -> List[Dict]:
    """Return the camera's zones with their live counts, for drawing every frame."""
    runtime = _get_runtime(camera_id)
    with runtime.lock:
        _refresh_zone_defs(runtime, camera_id)
        return _snapshot(runtime)


def update(camera_id: int, person_boxes, width: int, height: int) -> List[Dict]:
    """Advance tracking with the latest person boxes and persist new entries.

    Returns the same shape as :func:`snapshot` so the caller can draw immediately.
    """
    runtime = _get_runtime(camera_id)
    with runtime.lock:
        _refresh_zone_defs(runtime, camera_id)
        if not runtime.zone_defs:
            return []

        tracks = runtime.tracker.update(person_boxes)
        zones_norm = {
            zone_id: (zone['x1'], zone['y1'], zone['x2'], zone['y2'])
            for zone_id, zone in runtime.zone_defs.items()
        }
        entries = runtime.zone_counter.update(tracks, zones_norm, width, height)

        changed = {zid: n for zid, n in entries.items() if n}
        if changed:
            from .models import CountingZone

            now = timezone.now()
            for zone_id, n in changed.items():
                runtime.counts[zone_id] = runtime.counts.get(zone_id, 0) + n
                CountingZone.objects.filter(id=zone_id).update(
                    count=runtime.counts[zone_id], updated_at=now
                )

        return _snapshot(runtime)


def reset_zone(camera_id: int, zone_id: int) -> None:
    """Zero the in-memory running count for a zone (DB row reset by the caller)."""
    with _GLOBAL_LOCK:
        runtime = _RUNTIMES.get(camera_id)
    if runtime is None:
        return
    with runtime.lock:
        if zone_id in runtime.counts:
            runtime.counts[zone_id] = 0


def clear_camera(camera_id: int) -> None:
    """Drop all runtime state for a camera (e.g. when its stream stops)."""
    with _GLOBAL_LOCK:
        _RUNTIMES.pop(camera_id, None)
