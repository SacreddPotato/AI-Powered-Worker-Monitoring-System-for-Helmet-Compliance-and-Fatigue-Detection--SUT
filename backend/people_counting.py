"""Pure-Python people tracking and zone-entry counting.

This module deliberately has **no** OpenCV / Django / ML imports so the counting
logic can be unit-tested in isolation and reused from any thread.

Two collaborating pieces:

* :class:`CentroidTracker` assigns stable integer ids to person bounding boxes
  across successive inference cycles, using greedy nearest-centroid matching.
* :class:`ZoneCounter` watches those tracks and counts an *entry event* each time
  a track crosses from outside to inside a counting zone.  A person who lingers
  inside is only counted once; a person who leaves and returns is counted again.

Zones are expressed as ``(x1, y1, x2, y2)`` rectangles in **normalized** [0, 1]
coordinates so they survive changes in capture resolution and display size.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Hashable, Iterable, Sequence, Set, Tuple

Box = Sequence[float]  # (x1, y1, x2, y2[, confidence...]) in pixels
Zone = Tuple[float, float, float, float]  # normalized (x1, y1, x2, y2)


def centroid(box: Box) -> Tuple[float, float]:
    """Return the pixel centre ``(cx, cy)`` of a bounding box."""
    x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def point_in_norm_rect(cx: float, cy: float, zone: Zone, width: float, height: float) -> bool:
    """Whether pixel point ``(cx, cy)`` falls inside ``zone`` on a ``width``x``height`` frame.

    ``zone`` is normalized; the boundary is treated as inside.
    """
    if width <= 0 or height <= 0:
        return False
    zx1, zy1, zx2, zy2 = zone
    px1, px2 = sorted((zx1 * width, zx2 * width))
    py1, py2 = sorted((zy1 * height, zy2 * height))
    return px1 <= cx <= px2 and py1 <= cy <= py2


@dataclass
class Track:
    """A tracked person between inference cycles."""

    track_id: int
    cx: float
    cy: float
    misses: int = 0


class CentroidTracker:
    """Associate person detections across cycles by nearest centroid.

    Args:
        max_distance: maximum pixel distance for a detection to be considered the
            same person as an existing track.
        max_misses: how many consecutive cycles a track may go unmatched before it
            is dropped (tolerates brief detector dropouts / occlusion).
    """

    def __init__(self, max_distance: float = 80.0, max_misses: int = 5):
        self.max_distance = float(max_distance)
        self.max_misses = int(max_misses)
        self._next_id = 1
        self.tracks: Dict[int, Track] = {}

    def update(self, boxes: Iterable[Box]) -> Dict[int, Track]:
        """Advance the tracker by one cycle and return the live tracks."""
        detections = [centroid(b) for b in boxes]

        # Build all (distance, track_id, detection_index) candidate matches within
        # range, then assign greedily from closest to furthest.
        candidates = []
        for tid, track in self.tracks.items():
            for di, (cx, cy) in enumerate(detections):
                dist = ((track.cx - cx) ** 2 + (track.cy - cy) ** 2) ** 0.5
                if dist <= self.max_distance:
                    candidates.append((dist, tid, di))
        candidates.sort(key=lambda c: c[0])

        matched_tracks: Set[int] = set()
        matched_dets: Set[int] = set()
        for _dist, tid, di in candidates:
            if tid in matched_tracks or di in matched_dets:
                continue
            matched_tracks.add(tid)
            matched_dets.add(di)
            track = self.tracks[tid]
            track.cx, track.cy = detections[di]
            track.misses = 0

        # Age out tracks that were not matched this cycle.
        for tid in list(self.tracks):
            if tid not in matched_tracks:
                self.tracks[tid].misses += 1
                if self.tracks[tid].misses > self.max_misses:
                    del self.tracks[tid]

        # Spawn tracks for detections that matched nothing.
        for di, (cx, cy) in enumerate(detections):
            if di not in matched_dets:
                self.tracks[self._next_id] = Track(track_id=self._next_id, cx=cx, cy=cy)
                self._next_id += 1

        return self.tracks


class ZoneCounter:
    """Count outside->inside transitions of tracks through normalized zones."""

    def __init__(self) -> None:
        # track_id -> set of zone keys the track is currently inside
        self._inside: Dict[int, Set[Hashable]] = {}

    def update(
        self,
        tracks: Dict[int, Track],
        zones: Dict[Hashable, Zone],
        width: float,
        height: float,
    ) -> Dict[Hashable, int]:
        """Return the number of *new* entries per zone for this cycle.

        Args:
            tracks: mapping of ``track_id -> Track`` (e.g. ``CentroidTracker.tracks``).
            zones: mapping of an opaque zone key -> normalized rectangle.
            width, height: current frame size in pixels.
        """
        entries: Dict[Hashable, int] = {key: 0 for key in zones}

        live_ids = set(tracks)
        for tid in list(self._inside):
            if tid not in live_ids:
                del self._inside[tid]

        for tid, track in tracks.items():
            previously_inside = self._inside.get(tid, set())
            now_inside: Set[Hashable] = set()
            for key, zone in zones.items():
                if point_in_norm_rect(track.cx, track.cy, zone, width, height):
                    now_inside.add(key)
                    if key not in previously_inside:
                        entries[key] += 1
            self._inside[tid] = now_inside

        return entries

    def forget(self, zone_key: Hashable) -> None:
        """Drop any remembered inside-state for a zone that no longer exists."""
        for inside in self._inside.values():
            inside.discard(zone_key)
