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
