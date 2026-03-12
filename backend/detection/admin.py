from django.contrib import admin
from .models import ModelSetting, CameraModel, Detection

@admin.register(ModelSetting)
class ModelSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'is_enabled']

@admin.register(CameraModel)
class CameraModelAdmin(admin.ModelAdmin):
    list_display = ['camera', 'model_setting', 'is_enabled']
    list_filter = ['is_enabled', 'model_setting']

@admin.register(Detection)
class DetectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'camera', 'model_key', 'status', 'detected', 'confidence', 'created_at']
    list_filter = ['model_key', 'status', 'detected']
    ordering = ['-created_at']
