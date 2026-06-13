from django.db import models

class Camera(models.Model):
    name = models.CharField(max_length=255)
    source_url = models.CharField(max_length=500)
    location = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.source_url})"


class CountingZone(models.Model):
    """A user-drawn rectangle on a camera feed that counts how many people pass
    through it.

    Coordinates are stored normalized (0..1) relative to the frame so the zone
    maps correctly regardless of capture resolution or display size.  ``count`` is
    the cumulative number of entry events (a person crossing from outside to
    inside) and is persisted so it survives server restarts; it can be zeroed via
    the per-zone reset endpoint.
    """

    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='counting_zones')
    name = models.CharField(max_length=120, blank=True, default='Zone')
    x1 = models.FloatField()
    y1 = models.FloatField()
    x2 = models.FloatField()
    y2 = models.FloatField()
    count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.camera_id}:{self.name} ({self.count})"
