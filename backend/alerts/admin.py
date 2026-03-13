from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'severity', 'model_key', 'camera', 'status', 'message', 'created_at']
    list_filter = ['severity', 'status', 'model_key']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'acknowledged_at']
