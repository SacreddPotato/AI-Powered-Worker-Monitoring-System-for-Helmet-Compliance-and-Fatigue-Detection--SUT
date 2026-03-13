from django.db import models
from cameras.models import Camera
from detection.models import Detection

class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
    ]

    detection = models.ForeignKey(Detection, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='alerts')
    model_key = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='low')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    message = models.TextField()
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['camera']),
            models.Index(fields=['severity']),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.message} ({self.camera.name})"
