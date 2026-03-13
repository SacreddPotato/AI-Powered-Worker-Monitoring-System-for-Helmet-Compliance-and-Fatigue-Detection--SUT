from django.db import models
from cameras.models import Camera

class ModelSetting(models.Model):
    key = models.CharField(max_length=50, unique=True, primary_key=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.key

class CameraModel(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='model_overrides')
    model_setting = models.ForeignKey(ModelSetting, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ['camera', 'model_setting']

    def __str__(self):
        return f"{self.camera.name} -> {self.model_setting.key} ({'on' if self.is_enabled else 'off'})"

class Detection(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='detections')
    model_key = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    confidence = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, default='ok', choices=[
        ('ok', 'OK'),
        ('error', 'Error'),
        ('unavailable', 'Unavailable'),
    ])
    detected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['camera']),
        ]
