from django.contrib import admin
from .models import DevVideo

@admin.register(DevVideo)
class DevVideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_filename', 'file_size', 'duration', 'uploaded_at']
    ordering = ['-uploaded_at']
