"""Unit tests for the pure-Python people tracking / zone-entry counting engine.

These tests intentionally avoid any cv2 / ML / Django dependency so they run in
any interpreter that can import ``people_counting``.
"""
import people_counting as pc


def test_centroid_of_box():
    assert pc.centroid((0, 0, 10, 20)) == (5.0, 10.0)
    assert pc.centroid((10, 10, 30, 30, 0.9)) == (20.0, 20.0)


def test_point_in_norm_rect_maps_normalized_to_pixels():
    zone = (0.25, 0.25, 0.75, 0.75)  # centre half of a 100x100 frame -> 25..75
    assert pc.point_in_norm_rect(50, 50, zone, 100, 100) is True
    assert pc.point_in_norm_rect(10, 50, zone, 100, 100) is False  # left of zone
    assert pc.point_in_norm_rect(50, 90, zone, 100, 100) is False  # below zone
    # boundary is inclusive
    assert pc.point_in_norm_rect(25, 25, zone, 100, 100) is True


def test_point_in_norm_rect_handles_degenerate_frame():
    assert pc.point_in_norm_rect(5, 5, (0, 0, 1, 1), 0, 0) is False


def test_tracker_keeps_stable_id_for_small_movement():
    tracker = pc.CentroidTracker(max_distance=80, max_misses=3)
    tracks = tracker.update([(0, 0, 20, 20)])
    (first_id,) = tracks.keys()

    # Same person nudged a few pixels -> same id, no new track
    tracks = tracker.update([(4, 4, 24, 24)])
    assert list(tracks.keys()) == [first_id]


def test_tracker_assigns_new_id_for_new_detection():
    tracker = pc.CentroidTracker(max_distance=40, max_misses=3)
    tracker.update([(0, 0, 20, 20)])
    tracks = tracker.update([(0, 0, 20, 20), (200, 200, 220, 220)])
    assert len(tracks) == 2


def test_tracker_expires_track_after_max_misses():
    tracker = pc.CentroidTracker(max_distance=40, max_misses=2)
    tracker.update([(0, 0, 20, 20)])
    tracker.update([])  # miss 1
    assert len(tracker.tracks) == 1
    tracker.update([])  # miss 2
    assert len(tracker.tracks) == 1
    tracker.update([])  # miss 3 -> exceeds max_misses
    assert len(tracker.tracks) == 0


def test_zone_counter_counts_entry_once_while_inside():
    tracker = pc.CentroidTracker(max_distance=80, max_misses=3)
    counter = pc.ZoneCounter()
    zones = {"z": (0.4, 0.4, 0.6, 0.6)}  # centre of a 100x100 frame

    # Person starts outside the zone (top-left corner)
    tracks = tracker.update([(0, 0, 10, 10)])
    assert counter.update(tracks, zones, 100, 100) == {"z": 0}

    # Walks into the zone -> +1
    tracks = tracker.update([(45, 45, 55, 55)])
    assert counter.update(tracks, zones, 100, 100) == {"z": 1}

    # Stays inside -> not recounted
    tracks = tracker.update([(46, 46, 56, 56)])
    assert counter.update(tracks, zones, 100, 100) == {"z": 0}


def test_zone_counter_recounts_on_reentry():
    tracker = pc.CentroidTracker(max_distance=120, max_misses=5)
    counter = pc.ZoneCounter()
    zones = {"z": (0.4, 0.4, 0.6, 0.6)}

    tracker.update([(0, 0, 10, 10)])
    counter.update(tracker.tracks, zones, 100, 100)

    # enter
    tracker.update([(50, 50, 60, 60)])
    assert counter.update(tracker.tracks, zones, 100, 100) == {"z": 1}
    # leave
    tracker.update([(0, 0, 10, 10)])
    assert counter.update(tracker.tracks, zones, 100, 100) == {"z": 0}
    # re-enter -> counts again
    tracker.update([(50, 50, 60, 60)])
    assert counter.update(tracker.tracks, zones, 100, 100) == {"z": 1}


def test_zone_counter_tracks_multiple_zones_independently():
    tracker = pc.CentroidTracker(max_distance=200, max_misses=5)
    counter = pc.ZoneCounter()
    zones = {
        "left": (0.0, 0.0, 0.4, 1.0),
        "right": (0.6, 0.0, 1.0, 1.0),
    }

    # one person in the left zone, one in the right zone
    tracker.update([(10, 50, 30, 70), (80, 50, 95, 70)])
    entries = counter.update(tracker.tracks, zones, 100, 100)
    assert entries == {"left": 1, "right": 1}


def test_walk_through_sequence_counts_one_person_once():
    tracker = pc.CentroidTracker(max_distance=60, max_misses=4)
    counter = pc.ZoneCounter()
    zones = {"gate": (0.4, 0.0, 0.6, 1.0)}  # vertical strip in the middle

    total = 0
    # Person walks left -> right across the frame; centre x goes 5..95
    for cx in range(5, 100, 10):
        tracker.update([(cx - 5, 45, cx + 5, 55)])
        total += counter.update(tracker.tracks, zones, 100, 100)["gate"]

    assert total == 1
