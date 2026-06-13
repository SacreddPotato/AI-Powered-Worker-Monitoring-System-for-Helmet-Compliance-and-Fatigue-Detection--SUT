"""API + integration tests for the people-counting zone feature.

These are all non-ML: person detection is never exercised here (the counting
manager is driven directly with synthetic person boxes), so the suite runs in the
lightweight environment without torch / ultralytics.
"""
import numpy as np
import pytest


@pytest.mark.django_db
def test_zone_crud_flow(client):
    from cameras.models import Camera

    camera = Camera.objects.create(name="Gate", source_url="0", location="Yard")

    # Create
    create = client.post(
        f"/api/v1/cameras/{camera.id}/zones/",
        {"name": "Entrance", "x1": 0.1, "y1": 0.1, "x2": 0.5, "y2": 0.6},
        content_type="application/json",
    )
    assert create.status_code == 201
    zone = create.json()
    assert zone["name"] == "Entrance"
    assert zone["count"] == 0
    zone_id = zone["id"]

    # List
    listing = client.get(f"/api/v1/cameras/{camera.id}/zones/")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    # Retrieve
    detail = client.get(f"/api/v1/cameras/{camera.id}/zones/{zone_id}/")
    assert detail.status_code == 200
    assert detail.json()["id"] == zone_id

    # Partial update (move one corner)
    patch = client.patch(
        f"/api/v1/cameras/{camera.id}/zones/{zone_id}/",
        {"name": "Main Entrance", "x2": 0.7},
        content_type="application/json",
    )
    assert patch.status_code == 200
    assert patch.json()["name"] == "Main Entrance"
    assert patch.json()["x2"] == 0.7

    # Delete
    delete = client.delete(f"/api/v1/cameras/{camera.id}/zones/{zone_id}/")
    assert delete.status_code == 204
    assert client.get(f"/api/v1/cameras/{camera.id}/zones/").json() == []


@pytest.mark.django_db
def test_zone_rejects_invalid_coordinates(client):
    from cameras.models import Camera

    camera = Camera.objects.create(name="Gate", source_url="0")

    # x1 >= x2
    bad_order = client.post(
        f"/api/v1/cameras/{camera.id}/zones/",
        {"x1": 0.8, "y1": 0.1, "x2": 0.2, "y2": 0.6},
        content_type="application/json",
    )
    assert bad_order.status_code == 400

    # out of [0, 1] range
    out_of_range = client.post(
        f"/api/v1/cameras/{camera.id}/zones/",
        {"x1": -0.1, "y1": 0.1, "x2": 1.4, "y2": 0.6},
        content_type="application/json",
    )
    assert out_of_range.status_code == 400


@pytest.mark.django_db
def test_zone_create_404_for_missing_camera(client):
    resp = client.post(
        "/api/v1/cameras/999999/zones/",
        {"x1": 0.1, "y1": 0.1, "x2": 0.5, "y2": 0.6},
        content_type="application/json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_zone_reset_zeroes_count(client):
    from cameras.models import Camera, CountingZone

    camera = Camera.objects.create(name="Gate", source_url="0")
    zone = CountingZone.objects.create(
        camera=camera, name="Z", x1=0.1, y1=0.1, x2=0.5, y2=0.6, count=42
    )

    resp = client.post(f"/api/v1/cameras/{camera.id}/zones/{zone.id}/reset/")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0
    zone.refresh_from_db()
    assert zone.count == 0


@pytest.mark.django_db
def test_counting_manager_increments_db_on_entry():
    from cameras.models import Camera, CountingZone
    from cameras import counting

    camera = Camera.objects.create(name="Gate", source_url="0")
    zone = CountingZone.objects.create(
        camera=camera, name="Mid", x1=0.4, y1=0.4, x2=0.6, y2=0.6, count=0
    )
    counting.clear_camera(camera.id)  # fresh runtime (PKs can repeat across tests)

    # Frame 1: one person outside the zone -> no entry.
    snap = counting.update(camera.id, [(10, 10, 30, 30, 0.9)], 100, 100)
    assert snap[0]["count"] == 0

    # Frame 2: same person now inside the zone -> +1 entry, persisted to the DB.
    snap = counting.update(camera.id, [(45, 45, 55, 55, 0.9)], 100, 100)
    assert snap[0]["count"] == 1

    # Staying inside does not recount.
    snap = counting.update(camera.id, [(46, 46, 56, 56, 0.9)], 100, 100)
    assert snap[0]["count"] == 1

    zone.refresh_from_db()
    assert zone.count == 1

    counting.clear_camera(camera.id)


@pytest.mark.django_db
def test_counting_manager_reset_clears_runtime():
    from cameras.models import Camera, CountingZone
    from cameras import counting

    camera = Camera.objects.create(name="Gate", source_url="0")
    zone = CountingZone.objects.create(
        camera=camera, name="Mid", x1=0.4, y1=0.4, x2=0.6, y2=0.6, count=0
    )
    counting.clear_camera(camera.id)

    counting.update(camera.id, [(10, 10, 30, 30, 0.9)], 100, 100)
    counting.update(camera.id, [(45, 45, 55, 55, 0.9)], 100, 100)
    assert counting.snapshot(camera.id)[0]["count"] == 1

    # Reset DB + runtime, mirroring the API reset path.
    zone.count = 0
    zone.save(update_fields=["count", "updated_at"])
    counting.reset_zone(camera.id, zone.id)
    assert counting.snapshot(camera.id)[0]["count"] == 0

    counting.clear_camera(camera.id)


def test_draw_counting_zones_preserves_shape_and_tolerates_empty():
    from annotation import draw_counting_zones

    frame = np.zeros((120, 160, 3), dtype=np.uint8)

    # Empty list is a no-op.
    assert draw_counting_zones(frame, []) is frame

    zones = [
        {"name": "Entrance", "x1": 0.1, "y1": 0.05, "x2": 0.6, "y2": 0.7, "count": 7},
        {"name": "Top", "x1": 0.0, "y1": 0.0, "x2": 0.3, "y2": 0.2, "count": 0},
    ]
    out = draw_counting_zones(frame, zones)
    assert out.shape == (120, 160, 3)
    # Something was actually drawn (magenta pixels present).
    assert out.sum() > 0
