# Sentinel Dashboard Overhaul Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the worker monitoring dashboard from Flask to Django (DRF + Channels) and rebuild the React frontend with a Tactical HUD aesthetic, real-time WebSocket alerts, flexible alert grouping, and a full Developer Lab.

**Architecture:** Django backend with 5 apps (core, cameras, detection, alerts, devlab) wrapping existing ML services. React + Vite + Tailwind CSS frontend with 4 pages (Feeds, Alerts, Models, Dev Lab). Django Channels with InMemoryChannelLayer for WebSocket real-time alert push.

**Tech Stack:** Django 5.x, Django REST Framework, Django Channels, React 18, Vite, Tailwind CSS, SQLite (via Django ORM), WebSocket (native browser API)

**Spec:** `docs/superpowers/specs/2026-03-12-dashboard-overhaul-design.md`

---

## File Structure

### Backend (new Django project: `backend/`)

```
backend/
  manage.py                          # Django management CLI
  sentinel/                          # Django project package
    __init__.py
    settings.py                      # Django config, installed apps, channels, DRF
    urls.py                          # Root URL conf (REST + static serving)
    asgi.py                          # ASGI entry (HTTP + WebSocket)
    wsgi.py                          # WSGI fallback
  cameras/
    __init__.py
    models.py                        # Camera model (ORM)
    serializers.py                   # DRF serializers
    views.py                         # Camera CRUD + stream + status views
    urls.py                          # Camera URL patterns
    admin.py                         # Django admin registration
    services.py                      # Wraps existing camera_service.py
  detection/
    __init__.py
    models.py                        # Detection, ModelSetting, CameraModel models
    serializers.py                   # DRF serializers
    views.py                         # Analyze endpoint, model CRUD
    urls.py                          # Detection URL patterns
    admin.py                         # Django admin registration
    services.py                      # Wraps inference_service.py, model_service.py
  alerts/
    __init__.py
    models.py                        # Alert model
    serializers.py                   # DRF serializers
    views.py                         # Alert list, acknowledge
    urls.py                          # Alert URL patterns
    admin.py                         # Django admin registration
    consumers.py                     # WebSocket consumer (Channels)
    routing.py                       # WebSocket URL routing
    services.py                      # Alert creation + broadcast logic
  devlab/
    __init__.py
    models.py                        # DevVideo model
    serializers.py                   # DRF serializers
    views.py                         # Video upload, analyze, stream, thresholds, perf
    urls.py                          # Dev lab URL patterns
    admin.py                         # Django admin registration
  config.py                          # KEPT: model definitions, paths, thresholds
  camera_service.py                  # KEPT: camera capture logic (unchanged)
  inference_service.py               # KEPT: ML inference adapters (unchanged)
  fatigue_engine.py                  # KEPT: fatigue scoring (unchanged)
  model_service.py                   # KEPT: model enable/disable logic (unchanged)
  alerts_service.py                  # KEPT: alert severity mapping (unchanged)
  ml_models/                         # KEPT: model weights
  uploads/                           # KEPT: video uploads
```

### Frontend (rebuilt: `frontend/src/`)

```
frontend/
  package.json                       # Updated with tailwind, react-router
  tailwind.config.js                 # Tactical HUD theme config
  postcss.config.js                  # PostCSS for Tailwind
  vite.config.js                     # Updated proxy config
  index.html                         # Updated with fonts
  src/
    main.jsx                         # React entry, router setup
    App.jsx                          # Shell layout (icon rail + page outlet)
    index.css                        # Tailwind base + custom utilities
    api.js                           # REST API client (updated endpoints)
    ws.js                            # WebSocket client (alerts)
    hooks/
      useAlerts.js                   # Alert state + WebSocket integration
      useCameras.js                  # Camera state + polling
      useModels.js                   # Model state management
    components/
      IconRail.jsx                   # Left navigation rail
      Toast.jsx                      # Toast notification system
      AlertCard.jsx                  # Alert card (sidebar + table variants)
      CameraFeed.jsx                 # Single camera feed with badge overlays
      Toggle.jsx                     # Toggle switch component
      Badge.jsx                      # Status badge component
    pages/
      FeedsPage.jsx                  # Camera wall + alert sidebar
      AlertsPage.jsx                 # Alert table + detail panel
      ModelsPage.jsx                 # Global + per-camera model config
      DevLabPage.jsx                 # Dev lab with sub-tabs
```

---

## Chunk 1: Django Backend Scaffold + Core App

### Task 1: Initialize Django project

**Files:**
- Create: `backend/sentinel/__init__.py`
- Create: `backend/sentinel/settings.py`
- Create: `backend/sentinel/urls.py`
- Create: `backend/sentinel/asgi.py`
- Create: `backend/sentinel/wsgi.py`
- Create: `backend/manage.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Update requirements.txt**

Replace Flask with Django dependencies:

```
django>=5.0
djangorestframework
django-cors-headers
channels
daphne
opencv-python-headless
ultralytics
torch
torchvision
numpy
dlib
scipy
imutils
werkzeug
pillow
huggingface-hub
```

- [ ] **Step 2: Install new dependencies**

Run: `conda activate fatigue_env && pip install django djangorestframework django-cors-headers channels daphne`

- [ ] **Step 3: Create Django project structure**

Create `backend/manage.py`:

```python
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinel.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

Create `backend/sentinel/__init__.py` (empty).

Create `backend/sentinel/settings.py`:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-insecure-key-change-in-production')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    'cameras',
    'detection',
    'alerts',
    'devlab',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'sentinel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = 'sentinel.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'monitoring.db',
    }
}

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
}

CORS_ALLOW_ALL_ORIGINS = DEBUG

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / '..' / 'frontend' / 'dist']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_ROOT = BASE_DIR / 'uploads'
MEDIA_URL = '/uploads/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Frontend SPA serving
FRONTEND_DIR = BASE_DIR / '..' / 'frontend' / 'dist'
```

Create `backend/sentinel/asgi.py`:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinel.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from alerts.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': URLRouter(websocket_urlpatterns),
})
```

Create `backend/sentinel/wsgi.py`:

```python
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinel.settings')
application = get_wsgi_application()
```

Create `backend/sentinel/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.http import FileResponse

def health_check(request):
    from django.http import JsonResponse
    return JsonResponse({
        'status': 'ok',
        'service': 'sentinel-dashboard',
        'frontend_ready': settings.FRONTEND_DIR.exists(),
    })

def serve_frontend(request, path=''):
    frontend_dir = settings.FRONTEND_DIR
    file_path = frontend_dir / path
    if file_path.is_file():
        return FileResponse(open(file_path, 'rb'))
    index = frontend_dir / 'index.html'
    if index.is_file():
        return FileResponse(open(index, 'rb'), content_type='text/html')
    from django.http import HttpResponse
    return HttpResponse('Frontend not built. Run: cd frontend && npm run build', status=503)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health/', health_check, name='health'),
    path('api/v1/', include('cameras.urls')),
    path('api/v1/', include('detection.urls')),
    path('api/v1/', include('alerts.urls')),
    path('api/v1/', include('devlab.urls')),
    re_path(r'^(?P<path>.*)$', serve_frontend),
]
```

- [ ] **Step 4: Create empty app packages**

Create these `__init__.py` files (all empty):
- `backend/cameras/__init__.py`
- `backend/detection/__init__.py`
- `backend/alerts/__init__.py`
- `backend/devlab/__init__.py`

Create stub files for each app so Django can discover them. Each app needs a minimal `models.py`, `urls.py`, `views.py`, and `admin.py`.

For each of cameras, detection, alerts, devlab — create:

`<app>/urls.py`:
```python
from django.urls import path
urlpatterns = []
```

`<app>/models.py`:
```python
from django.db import models
```

`<app>/views.py`:
```python
# Views will be added in subsequent tasks
```

`<app>/admin.py`:
```python
from django.contrib import admin
```

Also create `alerts/routing.py`:
```python
from django.urls import path
websocket_urlpatterns = []
```

And `alerts/consumers.py`:
```python
# WebSocket consumer will be added in Task 7
```

- [ ] **Step 5: Verify Django boots**

Run: `cd backend && conda activate fatigue_env && python manage.py check`
Expected: `System check identified no issues.`

- [ ] **Step 6: Commit**

```bash
git add backend/manage.py backend/sentinel/ backend/cameras/__init__.py backend/cameras/urls.py backend/cameras/models.py backend/cameras/views.py backend/cameras/admin.py backend/detection/__init__.py backend/detection/urls.py backend/detection/models.py backend/detection/views.py backend/detection/admin.py backend/alerts/__init__.py backend/alerts/urls.py backend/alerts/models.py backend/alerts/views.py backend/alerts/admin.py backend/alerts/routing.py backend/alerts/consumers.py backend/devlab/__init__.py backend/devlab/urls.py backend/devlab/models.py backend/devlab/views.py backend/devlab/admin.py requirements.txt
git commit -m "feat: scaffold Django project with core, cameras, detection, alerts, devlab apps"
```

---

### Task 2: Cameras app — models, serializers, views

**Files:**
- Create: `backend/cameras/models.py`
- Create: `backend/cameras/serializers.py`
- Create: `backend/cameras/views.py`
- Create: `backend/cameras/services.py`
- Create: `backend/cameras/urls.py`
- Create: `backend/cameras/admin.py`

- [ ] **Step 1: Define Camera model**

`backend/cameras/models.py`:

```python
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
```

- [ ] **Step 2: Create and run migration**

Run: `cd backend && python manage.py makemigrations cameras && python manage.py migrate`

- [ ] **Step 3: Create serializer**

`backend/cameras/serializers.py`:

```python
from rest_framework import serializers
from .models import Camera

class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ['id', 'name', 'source_url', 'location', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
```

- [ ] **Step 4: Create service wrapper**

`backend/cameras/services.py`:

```python
"""Wraps existing camera_service.py for Django views."""
import sys
import os

# Add backend dir to path so we can import the existing service
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from camera_service import CameraService as _CameraService

# Singleton instance
_service = _CameraService()

def get_camera_service():
    return _service
```

- [ ] **Step 5: Create views**

`backend/cameras/views.py`:

```python
import cv2
from django.http import StreamingHttpResponse, JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Camera
from .serializers import CameraSerializer
from .services import get_camera_service

class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        camera = self.get_object()
        svc = get_camera_service()
        result = svc.check_camera_status(camera.source_url)
        return Response(result)

    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        camera = self.get_object()
        annotated = request.query_params.get('annotated', '0') == '1'
        svc = get_camera_service()

        def generate():
            for frame_bytes in svc.stream_frames(camera.source_url, camera.id, annotated=annotated):
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        return StreamingHttpResponse(
            generate(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
```

- [ ] **Step 6: Wire up URLs**

`backend/cameras/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CameraViewSet

router = DefaultRouter()
router.register(r'cameras', CameraViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

- [ ] **Step 7: Register admin**

`backend/cameras/admin.py`:

```python
from django.contrib import admin
from .models import Camera

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'source_url', 'location', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'location']
```

- [ ] **Step 8: Verify**

Run: `cd backend && python manage.py check && python manage.py runserver 7860`
Test: `curl http://localhost:7860/api/v1/cameras/`
Expected: `[]` (empty list)

- [ ] **Step 9: Commit**

```bash
git add backend/cameras/
git commit -m "feat: cameras app with model, DRF viewset, stream, and status endpoints"
```

---

### Task 3: Detection app — models, model management, analyze endpoint

**Files:**
- Create: `backend/detection/models.py`
- Create: `backend/detection/serializers.py`
- Create: `backend/detection/views.py`
- Create: `backend/detection/services.py`
- Create: `backend/detection/urls.py`
- Create: `backend/detection/admin.py`

- [ ] **Step 1: Define Detection models**

`backend/detection/models.py`:

```python
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
```

- [ ] **Step 2: Create and run migration**

Run: `cd backend && python manage.py makemigrations detection && python manage.py migrate`

- [ ] **Step 3: Create service wrapper**

`backend/detection/services.py`:

```python
"""Wraps existing inference_service.py and model_service.py."""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from inference_service import InferenceService as _InferenceService
from model_service import ModelService as _ModelService
from config import MODEL_DEFINITIONS

_inference_service = None
_model_service = None

def get_inference_service():
    global _inference_service
    if _inference_service is None:
        _inference_service = _InferenceService()
    return _inference_service

def get_model_service():
    global _model_service
    if _model_service is None:
        _model_service = _ModelService()
    return _model_service

def get_model_definitions():
    return MODEL_DEFINITIONS
```

- [ ] **Step 4: Create serializers**

`backend/detection/serializers.py`:

```python
from rest_framework import serializers
from .models import ModelSetting, CameraModel, Detection

class ModelSettingSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    health = serializers.SerializerMethodField()

    class Meta:
        model = ModelSetting
        fields = ['key', 'is_enabled', 'display_name', 'description', 'health']

    def get_display_name(self, obj):
        from .services import get_model_definitions
        defn = get_model_definitions().get(obj.key, {})
        return defn.get('display_name', obj.key)

    def get_description(self, obj):
        from .services import get_model_definitions
        defn = get_model_definitions().get(obj.key, {})
        return defn.get('description', '')

    def get_health(self, obj):
        from .services import get_inference_service
        svc = get_inference_service()
        return svc.get_model_health(obj.key)

class CameraModelSerializer(serializers.ModelSerializer):
    model_key = serializers.CharField(source='model_setting.key', read_only=True)

    class Meta:
        model = CameraModel
        fields = ['id', 'model_key', 'is_enabled']

class DetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detection
        fields = ['id', 'camera', 'model_key', 'payload', 'confidence', 'status', 'detected', 'created_at']
```

- [ ] **Step 5: Create views**

`backend/detection/views.py`:

```python
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ModelSetting, CameraModel, Detection
from .serializers import ModelSettingSerializer, CameraModelSerializer, DetectionSerializer
from .services import get_inference_service, get_model_definitions
from cameras.models import Camera

class ModelSettingViewSet(viewsets.ModelViewSet):
    queryset = ModelSetting.objects.all()
    serializer_class = ModelSettingSerializer
    lookup_field = 'key'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        is_enabled = request.data.get('enabled', request.data.get('is_enabled'))
        if is_enabled is not None:
            instance.is_enabled = bool(is_enabled)
            instance.save()
        return Response(ModelSettingSerializer(instance).data)

@api_view(['GET', 'PUT'])
def camera_models_view(request, camera_id, model_key=None):
    camera = Camera.objects.get(pk=camera_id)

    if model_key is None:
        # List all models for this camera
        overrides = CameraModel.objects.filter(camera=camera).select_related('model_setting')
        return Response(CameraModelSerializer(overrides, many=True).data)

    # Update specific camera-model override
    model_setting = ModelSetting.objects.get(key=model_key)
    override, _ = CameraModel.objects.get_or_create(camera=camera, model_setting=model_setting)
    is_enabled = request.data.get('enabled', request.data.get('is_enabled'))
    if is_enabled is not None:
        override.is_enabled = bool(is_enabled)
        override.save()
    return Response(CameraModelSerializer(override).data)

@api_view(['POST'])
def analyze_frame(request):
    """Run detection on a single frame from a camera."""
    camera_id = request.data.get('camera_id')
    if not camera_id:
        return Response({'error': 'camera_id required'}, status=status.HTTP_400_BAD_REQUEST)

    camera = Camera.objects.get(pk=camera_id)
    svc = get_inference_service()

    # Get enabled models for this camera
    enabled = ModelSetting.objects.filter(is_enabled=True).values_list('key', flat=True)
    overrides = CameraModel.objects.filter(camera=camera).select_related('model_setting')
    override_map = {o.model_setting.key: o.is_enabled for o in overrides}

    results = []
    for key in enabled:
        if not override_map.get(key, True):
            continue
        result = svc.run_inference(key, camera.source_url, camera.id)
        det = Detection.objects.create(
            camera=camera,
            model_key=key,
            payload=result.get('payload', {}),
            confidence=result.get('confidence', 0.0),
            status=result.get('status', 'ok'),
            detected=result.get('detected', False),
        )
        results.append(DetectionSerializer(det).data)

    return Response(results)

class DetectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Detection.objects.all()
    serializer_class = DetectionSerializer
    filterset_fields = ['camera', 'model_key', 'status']
```

- [ ] **Step 6: Wire up URLs**

`backend/detection/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModelSettingViewSet, DetectionViewSet, camera_models_view, analyze_frame

router = DefaultRouter()
router.register(r'models', ModelSettingViewSet)
router.register(r'detections', DetectionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('cameras/<int:camera_id>/models/', camera_models_view, name='camera-models-list'),
    path('cameras/<int:camera_id>/models/<str:model_key>/', camera_models_view, name='camera-models-detail'),
    path('detections/analyze/', analyze_frame, name='analyze-frame'),
]
```

- [ ] **Step 7: Register admin**

`backend/detection/admin.py`:

```python
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
```

- [ ] **Step 8: Create data migration to seed model settings**

Run: `cd backend && python manage.py makemigrations detection --empty -n seed_model_settings`

Then edit the new migration file to add:

```python
def seed_models(apps, schema_editor):
    ModelSetting = apps.get_model('detection', 'ModelSetting')
    for key in ['helmet', 'fatigue', 'vest', 'gloves', 'goggles']:
        ModelSetting.objects.get_or_create(key=key, defaults={'is_enabled': True})

class Migration(migrations.Migration):
    dependencies = [...]  # auto-generated
    operations = [
        migrations.RunPython(seed_models, migrations.RunPython.noop),
    ]
```

Run: `cd backend && python manage.py migrate`

- [ ] **Step 9: Verify**

Run: `cd backend && python manage.py check`
Run: `cd backend && python manage.py shell -c "from detection.models import ModelSetting; print(ModelSetting.objects.count())"`
Expected: `5`

- [ ] **Step 10: Commit**

```bash
git add backend/detection/
git commit -m "feat: detection app with model settings, camera overrides, and analyze endpoint"
```

---

### Task 4: Alerts app — models, views, WebSocket consumer

**Files:**
- Create: `backend/alerts/models.py`
- Create: `backend/alerts/serializers.py`
- Create: `backend/alerts/views.py`
- Create: `backend/alerts/services.py`
- Create: `backend/alerts/urls.py`
- Create: `backend/alerts/admin.py`
- Create: `backend/alerts/consumers.py`
- Create: `backend/alerts/routing.py`

- [ ] **Step 1: Define Alert model**

`backend/alerts/models.py`:

```python
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
```

- [ ] **Step 2: Create and run migration**

Run: `cd backend && python manage.py makemigrations alerts && python manage.py migrate`

- [ ] **Step 3: Create alert service with broadcast**

`backend/alerts/services.py`:

```python
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alert

SEVERITY_MAP = {
    'helmet': 'high',
    'fatigue': 'high',
    'vest': 'medium',
    'gloves': 'low',
    'goggles': 'low',
}

def create_alert(camera, model_key, message, detection=None, payload=None):
    severity = SEVERITY_MAP.get(model_key, 'low')
    alert = Alert.objects.create(
        detection=detection,
        camera=camera,
        model_key=model_key,
        severity=severity,
        message=message,
        payload=payload or {},
    )
    broadcast_alert(alert)
    return alert

def broadcast_alert(alert):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        'alerts',
        {
            'type': 'alert.new',
            'alert': {
                'id': alert.id,
                'severity': alert.severity,
                'model_key': alert.model_key,
                'camera_id': alert.camera_id,
                'camera_name': alert.camera.name,
                'message': alert.message,
                'payload': alert.payload,
                'status': alert.status,
                'created_at': alert.created_at.isoformat(),
            }
        }
    )
```

- [ ] **Step 4: Create WebSocket consumer**

`backend/alerts/consumers.py`:

```python
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class AlertConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)('alerts', self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)('alerts', self.channel_name)

    def alert_new(self, event):
        self.send(text_data=json.dumps({
            'type': 'alert.new',
            'alert': event['alert'],
        }))

    def alert_acknowledged(self, event):
        self.send(text_data=json.dumps({
            'type': 'alert.acknowledged',
            'alert_id': event['alert_id'],
        }))
```

- [ ] **Step 5: Create WebSocket routing**

`backend/alerts/routing.py`:

```python
from django.urls import path
from .consumers import AlertConsumer

websocket_urlpatterns = [
    path('ws/alerts/', AlertConsumer.as_asgi()),
]
```

- [ ] **Step 6: Create serializer and views**

`backend/alerts/serializers.py`:

```python
from rest_framework import serializers
from .models import Alert

class AlertSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source='camera.name', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'detection', 'camera', 'camera_name', 'model_key',
            'severity', 'status', 'message', 'payload',
            'created_at', 'acknowledged_at',
        ]
```

`backend/alerts/views.py`:

```python
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alert
from .serializers import AlertSerializer

class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.select_related('camera').all()
    serializer_class = AlertSerializer
    filterset_fields = ['camera', 'model_key', 'severity', 'status']

    @action(detail=True, methods=['patch'], url_path='acknowledge')
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.save()

        # Broadcast acknowledgment
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'alerts',
                {'type': 'alert.acknowledged', 'alert_id': alert.id}
            )

        return Response(AlertSerializer(alert).data)
```

- [ ] **Step 7: Wire up URLs**

`backend/alerts/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertViewSet

router = DefaultRouter()
router.register(r'alerts', AlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

- [ ] **Step 8: Register admin**

`backend/alerts/admin.py`:

```python
from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'severity', 'model_key', 'camera', 'status', 'message', 'created_at']
    list_filter = ['severity', 'status', 'model_key']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'acknowledged_at']
```

- [ ] **Step 9: Verify**

Run: `cd backend && python manage.py makemigrations && python manage.py migrate && python manage.py check`
Expected: No issues

- [ ] **Step 10: Commit**

```bash
git add backend/alerts/
git commit -m "feat: alerts app with WebSocket consumer, broadcast, severity mapping"
```

---

### Task 5: Dev Lab app — video upload, analyze, thresholds, performance

**Files:**
- Create: `backend/devlab/models.py`
- Create: `backend/devlab/serializers.py`
- Create: `backend/devlab/views.py`
- Create: `backend/devlab/urls.py`
- Create: `backend/devlab/admin.py`

- [ ] **Step 1: Define DevVideo model**

`backend/devlab/models.py`:

```python
from django.db import models

class DevVideo(models.Model):
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(default=0)
    duration = models.FloatField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_filename} ({self.uploaded_at})"
```

- [ ] **Step 2: Create and run migration**

Run: `cd backend && python manage.py makemigrations devlab && python manage.py migrate`

- [ ] **Step 3: Create serializer**

`backend/devlab/serializers.py`:

```python
from rest_framework import serializers
from .models import DevVideo

class DevVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DevVideo
        fields = ['id', 'original_filename', 'file_size', 'duration', 'uploaded_at']

class ThresholdSerializer(serializers.Serializer):
    confidence = serializers.FloatField(required=False)
    fatigue_consecutive_frames = serializers.IntegerField(required=False)
    ear_threshold = serializers.FloatField(required=False)
    mar_threshold = serializers.FloatField(required=False)
    head_tilt_degrees = serializers.FloatField(required=False)
```

- [ ] **Step 4: Create views**

`backend/devlab/views.py`:

```python
import os
import time
import uuid
import cv2
import psutil
from django.conf import settings
from django.http import FileResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import DevVideo
from .serializers import DevVideoSerializer, ThresholdSerializer
from detection.services import get_inference_service, get_model_definitions

UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'dev_videos')

@api_view(['POST', 'GET'])
def videos_list(request):
    if request.method == 'GET':
        videos = DevVideo.objects.all().order_by('-uploaded_at')
        return Response(DevVideoSerializer(videos, many=True).data)

    file = request.FILES.get('video')
    if not file:
        return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{file.name}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)

    # Get duration with OpenCV
    cap = cv2.VideoCapture(filepath)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps > 0 else None
    cap.release()

    video = DevVideo.objects.create(
        original_filename=file.name,
        file_path=filepath,
        file_size=file.size,
        duration=duration,
    )
    return Response(DevVideoSerializer(video).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def video_file(request, video_id):
    video = DevVideo.objects.get(pk=video_id)
    return FileResponse(open(video.file_path, 'rb'), content_type='video/mp4')

@api_view(['GET'])
def video_stream(request, video_id):
    video = DevVideo.objects.get(pk=video_id)
    annotated = request.query_params.get('annotated', '0') == '1'

    def generate():
        cap = cv2.VideoCapture(video.file_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            _, buf = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        cap.release()

    return StreamingHttpResponse(
        generate(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

@api_view(['POST'])
def video_analyze(request, video_id):
    video = DevVideo.objects.get(pk=video_id)
    sample_every = int(request.data.get('sample_every_n_frames', 10))
    max_samples = int(request.data.get('max_samples', 50))

    svc = get_inference_service()
    cap = cv2.VideoCapture(video.file_path)

    results = []
    frame_idx = 0
    samples = 0

    while cap.isOpened() and samples < max_samples:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every == 0:
            # Run all enabled models on this frame
            from detection.models import ModelSetting
            enabled = ModelSetting.objects.filter(is_enabled=True).values_list('key', flat=True)
            frame_results = {}
            for key in enabled:
                result = svc.run_inference_on_frame(key, frame, camera_id=0)
                frame_results[key] = result
            results.append({'frame': frame_idx, 'detections': frame_results})
            samples += 1
        frame_idx += 1

    cap.release()
    return Response({
        'video_id': video.id,
        'frames_total': frame_idx,
        'frames_analyzed': samples,
        'results': results,
    })

@api_view(['GET', 'PUT'])
def thresholds_view(request):
    import config as cfg

    if request.method == 'GET':
        return Response({
            'confidence': cfg.DEFAULT_ALERT_CONFIDENCE_THRESHOLD,
            'fatigue_consecutive_frames': cfg.FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD,
            'ear_threshold': getattr(cfg, 'EAR_THRESHOLD', 0.21),
            'mar_threshold': getattr(cfg, 'MAR_THRESHOLD', 0.65),
            'head_tilt_degrees': cfg.HEAD_TILT_ALERT_DEGREES,
        })

    # Update thresholds in config (runtime only)
    data = request.data
    if 'confidence' in data:
        cfg.DEFAULT_ALERT_CONFIDENCE_THRESHOLD = float(data['confidence'])
    if 'fatigue_consecutive_frames' in data:
        cfg.FATIGUE_CONSECUTIVE_FRAMES_THRESHOLD = int(data['fatigue_consecutive_frames'])
    if 'ear_threshold' in data:
        cfg.EAR_THRESHOLD = float(data['ear_threshold'])
    if 'mar_threshold' in data:
        cfg.MAR_THRESHOLD = float(data['mar_threshold'])
    if 'head_tilt_degrees' in data:
        cfg.HEAD_TILT_ALERT_DEGREES = float(data['head_tilt_degrees'])

    return Response({'status': 'updated'})

@api_view(['GET'])
def performance_view(request):
    import torch
    gpu_available = torch.cuda.is_available()
    gpu_percent = 0
    if gpu_available:
        try:
            gpu_percent = torch.cuda.utilization()
        except Exception:
            gpu_percent = -1

    process = psutil.Process()
    mem = process.memory_info()

    return Response({
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_mb': round(mem.rss / 1024 / 1024, 1),
        'gpu_available': gpu_available,
        'gpu_percent': gpu_percent,
    })
```

- [ ] **Step 5: Wire up URLs**

`backend/devlab/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('dev/videos/', views.videos_list, name='dev-videos-list'),
    path('dev/videos/<int:video_id>/file/', views.video_file, name='dev-video-file'),
    path('dev/videos/<int:video_id>/stream/', views.video_stream, name='dev-video-stream'),
    path('dev/videos/<int:video_id>/analyze/', views.video_analyze, name='dev-video-analyze'),
    path('dev/thresholds/', views.thresholds_view, name='dev-thresholds'),
    path('dev/performance/', views.performance_view, name='dev-performance'),
]
```

- [ ] **Step 6: Register admin and add psutil to requirements**

`backend/devlab/admin.py`:

```python
from django.contrib import admin
from .models import DevVideo

@admin.register(DevVideo)
class DevVideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_filename', 'file_size', 'duration', 'uploaded_at']
    ordering = ['-uploaded_at']
```

Add `psutil` to `requirements.txt`.

- [ ] **Step 7: Verify**

Run: `cd backend && pip install psutil && python manage.py makemigrations && python manage.py migrate && python manage.py check`

- [ ] **Step 8: Commit**

```bash
git add backend/devlab/ requirements.txt
git commit -m "feat: devlab app with video upload, analysis, thresholds, and performance endpoints"
```

---

### Task 6: Delete old Flask app.py and database.py

**Files:**
- Delete: `backend/app.py` (replaced by Django views across all apps)
- Delete: `backend/database.py` (replaced by Django ORM models)

- [ ] **Step 1: Remove old files**

```bash
git rm backend/app.py backend/database.py
```

- [ ] **Step 2: Verify Django still works**

Run: `cd backend && python manage.py check`
Run: `cd backend && python manage.py runserver 7860`
Test: `curl http://localhost:7860/api/v1/health/`

- [ ] **Step 3: Update Dockerfile**

Replace the entrypoint in `Dockerfile`:

From: `CMD ["python", "backend/app.py"]`
To: `CMD ["daphne", "-b", "0.0.0.0", "-p", "7860", "sentinel.asgi:application"]`

Also add `WORKDIR /app/backend` before the CMD so Django can find manage.py.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove Flask app.py and database.py, update Dockerfile for Django"
```

---

## Chunk 2: Frontend — Tailwind Setup + Shell + Components

### Task 7: Frontend scaffold — Tailwind, Router, fonts

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Modify: `frontend/index.html`
- Modify: `frontend/vite.config.js`
- Create: `frontend/src/index.css`
- Modify: `frontend/src/main.jsx`

- [ ] **Step 1: Install Tailwind and React Router**

Run:
```bash
cd frontend
npm install react-router-dom
npm install -D tailwindcss @tailwindcss/vite
```

- [ ] **Step 2: Update vite.config.js**

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:7860",
      "/ws": {
        target: "ws://localhost:7860",
        ws: true,
      },
    },
  },
});
```

- [ ] **Step 3: Create Tailwind config**

`frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      colors: {
        surface: "#18181b",
        "surface-alt": "#111113",
      },
      animation: {
        "pulse-dot": "pulse-dot 2s ease-in-out infinite",
        "scan": "scan 4s ease-in-out infinite",
        "slide-in": "slide-in 0.3s ease",
      },
      keyframes: {
        "pulse-dot": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.3" },
        },
        scan: {
          "0%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(100%)" },
          "100%": { transform: "translateY(0)" },
        },
        "slide-in": {
          from: { opacity: "0", transform: "translateX(20px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
      },
    },
  },
  plugins: [],
};
```

`frontend/postcss.config.js`:

```javascript
export default {
  plugins: {
    tailwindcss: {},
  },
};
```

- [ ] **Step 4: Create base CSS**

`frontend/src/index.css`:

```css
@import "tailwindcss";

@theme {
  --font-sans: "DM Sans", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", monospace;
  --color-surface: #18181b;
  --color-surface-alt: #111113;
}

/* Scrollbar styling */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #27272a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3f3f46; }

/* Grid background for body */
body {
  background-color: #09090b;
  background-image:
    linear-gradient(rgba(59, 130, 246, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.02) 1px, transparent 1px);
  background-size: 28px 28px;
}
```

- [ ] **Step 5: Update index.html**

`frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sentinel — Worker Monitoring</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  </head>
  <body class="font-sans text-zinc-100 antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Update main.jsx**

`frontend/src/main.jsx`:

```jsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

- [ ] **Step 7: Delete old styles.css**

Remove `frontend/src/styles.css` — replaced by Tailwind.

- [ ] **Step 8: Verify**

Run: `cd frontend && npm run dev`
Expected: Vite starts on port 5173, blank page loads without errors

- [ ] **Step 9: Commit**

```bash
cd frontend
git add package.json package-lock.json tailwind.config.js postcss.config.js vite.config.js index.html src/main.jsx src/index.css
git rm src/styles.css
git commit -m "feat: frontend scaffold with Tailwind CSS, React Router, and DM Sans/JetBrains Mono fonts"
```

---

### Task 8: Shell layout — App.jsx + IconRail + api.js + ws.js

**Files:**
- Rewrite: `frontend/src/App.jsx`
- Rewrite: `frontend/src/api.js`
- Create: `frontend/src/ws.js`
- Create: `frontend/src/components/IconRail.jsx`
- Create: `frontend/src/components/Toast.jsx`

- [ ] **Step 1: Create API client**

`frontend/src/api.js`:

```javascript
const BASE = "/api/v1";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  // Cameras
  listCameras: () => request("/cameras/"),
  createCamera: (data) => request("/cameras/", { method: "POST", body: JSON.stringify(data) }),
  updateCamera: (id, data) => request(`/cameras/${id}/`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCamera: (id) => request(`/cameras/${id}/`, { method: "DELETE" }),
  cameraStatus: (id) => request(`/cameras/${id}/status/`),
  cameraStreamUrl: (id, annotated = false) => `${BASE}/cameras/${id}/stream/${annotated ? "?annotated=1" : ""}`,

  // Models
  listModels: () => request("/models/"),
  updateModel: (key, data) => request(`/models/${key}/`, { method: "PUT", body: JSON.stringify(data) }),
  listCameraModels: (camId) => request(`/cameras/${camId}/models/`),
  updateCameraModel: (camId, key, data) => request(`/cameras/${camId}/models/${key}/`, { method: "PUT", body: JSON.stringify(data) }),

  // Alerts
  listAlerts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/alerts/${qs ? "?" + qs : ""}`);
  },
  acknowledgeAlert: (id) => request(`/alerts/${id}/acknowledge/`, { method: "PATCH" }),

  // Detections
  analyze: (cameraId) => request("/detections/analyze/", { method: "POST", body: JSON.stringify({ camera_id: cameraId }) }),

  // Dev Lab
  uploadVideo: (file) => {
    const form = new FormData();
    form.append("video", file);
    return fetch(`${BASE}/dev/videos/`, { method: "POST", body: form }).then((r) => r.json());
  },
  listVideos: () => request("/dev/videos/"),
  videoStreamUrl: (id, annotated = false) => `${BASE}/dev/videos/${id}/stream/${annotated ? "?annotated=1" : ""}`,
  analyzeVideo: (id, opts) => request(`/dev/videos/${id}/analyze/`, { method: "POST", body: JSON.stringify(opts) }),
  getThresholds: () => request("/dev/thresholds/"),
  updateThresholds: (data) => request("/dev/thresholds/", { method: "PUT", body: JSON.stringify(data) }),
  getPerformance: () => request("/dev/performance/"),
};
```

- [ ] **Step 2: Create WebSocket client**

`frontend/src/ws.js`:

```javascript
export function createAlertSocket(onMessage) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${window.location.host}/ws/alerts/`;
  let ws = null;
  let reconnectTimer = null;

  function connect() {
    ws = new WebSocket(url);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onMessage(data);
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };
    ws.onclose = () => {
      reconnectTimer = setTimeout(connect, 3000);
    };
    ws.onerror = () => ws.close();
  }

  connect();

  return {
    close() {
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
    },
  };
}
```

- [ ] **Step 3: Create IconRail**

`frontend/src/components/IconRail.jsx`:

```jsx
import { NavLink } from "react-router-dom";

const icons = {
  feeds: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="8" height="8" rx="1" /><rect x="14" y="3" width="8" height="8" rx="1" />
      <rect x="2" y="13" width="8" height="8" rx="1" /><rect x="14" y="13" width="8" height="8" rx="1" />
    </svg>
  ),
  alerts: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  ),
  models: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
  devlab: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
    </svg>
  ),
};

const navItems = [
  { to: "/", icon: "feeds", label: "Feeds" },
  { to: "/alerts", icon: "alerts", label: "Alerts" },
  { to: "/models", icon: "models", label: "Models" },
  { to: "/devlab", icon: "devlab", label: "Dev Lab" },
];

export default function IconRail({ alertCount = 0 }) {
  return (
    <nav className="w-14 bg-[#0c0c0f] border-r border-zinc-800/60 flex flex-col items-center py-3 gap-1.5 shrink-0">
      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-violet-500 rounded-lg flex items-center justify-center mb-4">
        <span className="text-white text-sm font-bold">S</span>
      </div>
      {navItems.map(({ to, icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/"}
          className={({ isActive }) =>
            `w-9 h-9 rounded-lg flex items-center justify-center relative transition-colors ${
              isActive ? "bg-blue-500/10 text-blue-400" : "text-zinc-600 hover:text-zinc-400 hover:bg-white/[0.03]"
            }`
          }
          title={label}
        >
          {icons[icon]}
          {icon === "alerts" && alertCount > 0 && (
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border-2 border-[#0c0c0f] animate-pulse-dot" />
          )}
        </NavLink>
      ))}
    </nav>
  );
}
```

- [ ] **Step 4: Create Toast component**

`frontend/src/components/Toast.jsx`:

```jsx
import { useEffect, useState } from "react";

const SEVERITY_STYLES = {
  high: "border-l-red-500",
  medium: "border-l-amber-500",
  low: "border-l-blue-500",
};

export default function Toast({ alerts, onDismiss }) {
  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
      {alerts.map((alert) => (
        <ToastItem key={alert.id} alert={alert} onDismiss={() => onDismiss(alert.id)} />
      ))}
    </div>
  );
}

function ToastItem({ alert, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 8000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div
      className={`pointer-events-auto bg-zinc-900 border border-zinc-800 rounded-lg p-3 min-w-[300px] animate-slide-in border-l-[3px] ${
        SEVERITY_STYLES[alert.severity] || "border-l-zinc-600"
      }`}
    >
      <div className="text-xs font-semibold text-zinc-50">{alert.message}</div>
      <div className="text-[10px] text-zinc-500 mt-1">
        {alert.camera_name} &middot; Just now
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Create App.jsx shell**

`frontend/src/App.jsx`:

```jsx
import { useState, useEffect, useCallback } from "react";
import { Routes, Route } from "react-router-dom";
import IconRail from "./components/IconRail";
import Toast from "./components/Toast";
import { createAlertSocket } from "./ws";
import { api } from "./api";

// Lazy page placeholders (will be built in Tasks 9-12)
function FeedsPage() {
  return <div className="flex-1 flex items-center justify-center text-zinc-600">Feeds — coming next</div>;
}
function AlertsPage() {
  return <div className="flex-1 flex items-center justify-center text-zinc-600">Alerts — coming next</div>;
}
function ModelsPage() {
  return <div className="flex-1 flex items-center justify-center text-zinc-600">Models — coming next</div>;
}
function DevLabPage() {
  return <div className="flex-1 flex items-center justify-center text-zinc-600">Dev Lab — coming next</div>;
}

export default function App() {
  const [toasts, setToasts] = useState([]);
  const [alertCount, setAlertCount] = useState(0);

  // Fetch initial alert count
  useEffect(() => {
    api.listAlerts({ status: "open", limit: 1 }).then((data) => {
      setAlertCount(data.count ?? data.results?.length ?? 0);
    }).catch(() => {});
  }, []);

  // WebSocket connection
  useEffect(() => {
    const socket = createAlertSocket((msg) => {
      if (msg.type === "alert.new") {
        setToasts((prev) => [...prev.slice(-4), msg.alert]);
        setAlertCount((c) => c + 1);
      }
      if (msg.type === "alert.acknowledged") {
        setAlertCount((c) => Math.max(0, c - 1));
      }
    });
    return () => socket.close();
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <div className="h-screen flex overflow-hidden">
      <IconRail alertCount={alertCount} />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Routes>
          <Route path="/" element={<FeedsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/devlab" element={<DevLabPage />} />
        </Routes>
      </main>
      <Toast alerts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
```

- [ ] **Step 6: Verify**

Run: `cd frontend && npm run dev`
Expected: Dark page with icon rail on left, placeholder text, icons navigate between routes

- [ ] **Step 7: Commit**

```bash
cd frontend
git add src/App.jsx src/api.js src/ws.js src/components/
git commit -m "feat: app shell with icon rail, routing, WebSocket client, and toast notifications"
```

---

## Chunk 3: Frontend Pages

### Task 9: Shared components — CameraFeed, AlertCard, Toggle, Badge

**Files:**
- Create: `frontend/src/components/CameraFeed.jsx`
- Create: `frontend/src/components/AlertCard.jsx`
- Create: `frontend/src/components/Toggle.jsx`
- Create: `frontend/src/components/Badge.jsx`

- [ ] **Step 1: Create all shared components**

`frontend/src/components/Badge.jsx`:

```jsx
const VARIANTS = {
  danger: "bg-red-500/15 text-red-300 border-red-500/25",
  warning: "bg-amber-500/12 text-amber-300 border-amber-500/20",
  success: "bg-green-500/10 text-green-300 border-green-500/20",
  info: "bg-blue-500/10 text-blue-300 border-blue-500/20",
  muted: "bg-zinc-800 text-zinc-400 border-zinc-700",
};

export default function Badge({ variant = "muted", children, className = "" }) {
  return (
    <span className={`text-[8px] font-semibold px-2 py-0.5 rounded border inline-block ${VARIANTS[variant]} ${className}`}>
      {children}
    </span>
  );
}
```

`frontend/src/components/Toggle.jsx`:

```jsx
export default function Toggle({ enabled, onChange, size = "md" }) {
  const sizes = {
    sm: { track: "w-7 h-4", dot: "w-2.5 h-2.5", translate: "translate-x-3" },
    md: { track: "w-9 h-5", dot: "w-3.5 h-3.5", translate: "translate-x-4" },
  };
  const s = sizes[size] || sizes.md;

  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`${s.track} rounded-full relative transition-colors cursor-pointer ${
        enabled ? "bg-blue-500/40" : "bg-zinc-700"
      }`}
    >
      <span
        className={`absolute top-0.5 left-0.5 ${s.dot} rounded-full transition-all ${
          enabled ? `${s.translate} bg-blue-400` : "bg-zinc-500"
        }`}
      />
    </button>
  );
}
```

`frontend/src/components/CameraFeed.jsx`:

```jsx
import Badge from "./Badge";
import { api } from "../api";

export default function CameraFeed({ camera, isHero = false, onClick, badges = [] }) {
  return (
    <div
      onClick={onClick}
      className={`bg-surface-alt border border-zinc-800 rounded-lg relative overflow-hidden cursor-pointer transition-colors hover:border-zinc-700 ${
        isHero ? "col-span-2" : ""
      }`}
    >
      {/* MJPEG stream */}
      <img
        src={api.cameraStreamUrl(camera.id, true)}
        alt={camera.name}
        className="absolute inset-0 w-full h-full object-cover"
        loading="lazy"
      />

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/80" />

      {/* Scan line on hero */}
      {isHero && (
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent animate-scan" />
      )}

      {/* Top bar */}
      <div className="absolute top-2.5 left-3 right-3 flex justify-between items-center z-10">
        <span className="text-[10px] font-semibold text-zinc-400">{camera.name}{camera.location ? ` — ${camera.location}` : ""}</span>
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse-dot" />
          <span className="text-[8px] text-red-500 font-semibold">LIVE</span>
        </div>
      </div>

      {/* Bottom badges */}
      <div className="absolute bottom-2.5 left-3 right-3 flex justify-between items-end z-10">
        <div className="flex gap-1 flex-wrap">
          {badges.map((b, i) => (
            <Badge key={i} variant={b.variant}>{b.label}</Badge>
          ))}
          {badges.length === 0 && <Badge variant="success">All clear</Badge>}
        </div>
      </div>
    </div>
  );
}
```

`frontend/src/components/AlertCard.jsx`:

```jsx
const SEV_STYLES = {
  high: { bg: "bg-red-500/5", border: "border-l-red-500", label: "text-red-400" },
  medium: { bg: "bg-amber-500/5", border: "border-l-amber-500", label: "text-amber-400" },
  low: { bg: "bg-blue-500/5", border: "border-l-blue-500", label: "text-blue-400" },
};

export default function AlertCard({ alert, compact = false, onClick }) {
  const s = SEV_STYLES[alert.severity] || SEV_STYLES.low;

  return (
    <div
      onClick={onClick}
      className={`${s.bg} border-l-[3px] ${s.border} rounded-lg p-2.5 cursor-pointer transition-colors hover:bg-white/[0.02] ${
        compact ? "mb-1.5" : "mb-2"
      }`}
    >
      <div className="text-[10px] font-semibold text-zinc-100">{alert.message}</div>
      {!compact && alert.payload?.description && (
        <div className="text-[9px] text-zinc-500 mt-1">{alert.payload.description}</div>
      )}
      <div className="text-[8px] text-zinc-600 mt-1">
        {alert.camera_name} &middot; {formatTime(alert.created_at)}
      </div>
    </div>
  );
}

function formatTime(iso) {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  return `${Math.round(diff / 3600)}h ago`;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: shared components — CameraFeed, AlertCard, Toggle, Badge"
```

---

### Task 10: Feeds page

**Files:**
- Create: `frontend/src/pages/FeedsPage.jsx`
- Modify: `frontend/src/App.jsx` (replace placeholder)

- [ ] **Step 1: Create FeedsPage**

`frontend/src/pages/FeedsPage.jsx`:

```jsx
import { useState, useEffect } from "react";
import { api } from "../api";
import CameraFeed from "../components/CameraFeed";
import AlertCard from "../components/AlertCard";

export default function FeedsPage() {
  const [cameras, setCameras] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [heroId, setHeroId] = useState(null);

  useEffect(() => {
    api.listCameras().then((data) => {
      const list = data.results || data;
      setCameras(list);
      if (list.length > 0 && !heroId) setHeroId(list[0].id);
    });
    api.listAlerts({ status: "open", limit: 20 }).then((data) => {
      setAlerts(data.results || data);
    });
    const interval = setInterval(() => {
      api.listAlerts({ status: "open", limit: 20 }).then((data) => setAlerts(data.results || data));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const hero = cameras.find((c) => c.id === heroId);
  const others = cameras.filter((c) => c.id !== heroId);

  // Group alerts by severity
  const grouped = { high: [], medium: [], low: [] };
  alerts.forEach((a) => (grouped[a.severity] || grouped.low).push(a));

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Live Feeds</h1>
          <span className="text-xs text-zinc-600">{cameras.length} cameras</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 bg-zinc-900 border border-zinc-800 rounded-full px-3 py-1">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_6px_rgba(34,197,94,.5)]" />
          All systems online
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Camera grid */}
        <div className="flex-1 p-3 overflow-auto">
          <div className="grid grid-cols-2 gap-2 h-full" style={{ gridTemplateRows: "1.6fr 1fr" }}>
            {hero && (
              <CameraFeed camera={hero} isHero badges={getBadges(alerts, hero.id)} />
            )}
            {others.slice(0, 2).map((cam) => (
              <CameraFeed
                key={cam.id}
                camera={cam}
                onClick={() => setHeroId(cam.id)}
                badges={getBadges(alerts, cam.id)}
              />
            ))}
          </div>
        </div>

        {/* Alert sidebar */}
        <div className="w-[280px] bg-[#0c0c0f] border-l border-zinc-800/60 flex flex-col shrink-0">
          <div className="px-3.5 py-3 border-b border-zinc-800/60 flex justify-between items-center">
            <span className="text-xs font-semibold text-zinc-400">Alerts</span>
            <span className="text-[9px] font-semibold bg-red-500/15 text-red-500 px-2 py-0.5 rounded-full">
              {alerts.length} active
            </span>
          </div>
          <div className="flex-1 overflow-y-auto px-2.5 py-2">
            {["high", "medium", "low"].map(
              (sev) =>
                grouped[sev].length > 0 && (
                  <div key={sev}>
                    <div className="text-[8px] text-zinc-600 uppercase tracking-widest px-1 py-1.5">
                      {sev === "high" ? "Critical" : sev === "medium" ? "Warning" : "Info"}
                    </div>
                    {grouped[sev].map((alert) => (
                      <AlertCard key={alert.id} alert={alert} compact />
                    ))}
                  </div>
                )
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function getBadges(alerts, cameraId) {
  return alerts
    .filter((a) => a.camera === cameraId)
    .map((a) => ({
      variant: a.severity === "high" ? "danger" : a.severity === "medium" ? "warning" : "info",
      label: a.message,
    }));
}
```

- [ ] **Step 2: Update App.jsx imports**

Replace the FeedsPage placeholder in `App.jsx`:
- Add: `import FeedsPage from "./pages/FeedsPage";`
- Remove the inline FeedsPage function

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/FeedsPage.jsx frontend/src/App.jsx
git commit -m "feat: Feeds page with camera wall, hero promotion, and alert sidebar"
```

---

### Task 11: Alerts page

**Files:**
- Create: `frontend/src/pages/AlertsPage.jsx`
- Modify: `frontend/src/App.jsx` (replace placeholder)

- [ ] **Step 1: Create AlertsPage**

`frontend/src/pages/AlertsPage.jsx`:

```jsx
import { useState, useEffect } from "react";
import { api } from "../api";

const GROUP_MODES = ["severity", "camera", "model", "time"];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [groupBy, setGroupBy] = useState("severity");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 5000);
    return () => clearInterval(interval);
  }, []);

  function loadAlerts() {
    api.listAlerts({ limit: 200 }).then((data) => setAlerts(data.results || data));
  }

  async function handleAcknowledge(id) {
    await api.acknowledgeAlert(id);
    loadAlerts();
    if (selected?.id === id) setSelected((s) => ({ ...s, status: "acknowledged" }));
  }

  const groups = groupAlerts(alerts, groupBy);
  const detail = selected || alerts[0];

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Alert Center</h1>
          <span className="text-xs text-zinc-600">
            {alerts.filter((a) => a.status === "open").length} active
          </span>
        </div>
        <div className="flex gap-1.5">
          {GROUP_MODES.map((mode) => (
            <button
              key={mode}
              onClick={() => setGroupBy(mode)}
              className={`px-3 py-1.5 rounded-lg border text-[10px] font-medium capitalize transition-colors ${
                groupBy === mode
                  ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                  : "bg-transparent text-zinc-500 border-zinc-800 hover:text-zinc-400"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Alert list */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {groups.map(({ label, items, count }) => (
            <div key={label} className="mb-4">
              <div className="flex justify-between items-center text-[9px] text-zinc-600 uppercase tracking-widest pb-1.5 mb-2 border-b border-zinc-800/60">
                <span>{label}</span>
                <span>{count} alerts</span>
              </div>
              {items.map((alert) => (
                <div
                  key={alert.id}
                  onClick={() => setSelected(alert)}
                  className={`grid grid-cols-[6px_1fr_140px_100px_80px] gap-3 items-center px-3 py-2.5 rounded-lg mb-1 cursor-pointer transition-colors ${
                    selected?.id === alert.id ? "bg-white/[0.03]" : "hover:bg-white/[0.02]"
                  }`}
                >
                  <div className={`w-1 h-7 rounded-sm ${sevColor(alert.severity)}`} />
                  <div>
                    <div className="text-[11px] font-medium text-zinc-100">{alert.message}</div>
                    <div className="text-[9px] text-zinc-600 mt-0.5">{alert.model_key} detection</div>
                  </div>
                  <div className="text-[10px] text-zinc-500">{alert.camera_name}</div>
                  <div className="text-[10px] text-zinc-600">{formatTime(alert.created_at)}</div>
                  {alert.status === "open" ? (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleAcknowledge(alert.id); }}
                      className="text-[9px] text-blue-400 bg-blue-500/8 border border-blue-500/20 px-2.5 py-1 rounded-md text-center hover:bg-blue-500/15"
                    >
                      Acknowledge
                    </button>
                  ) : (
                    <span className="text-[9px] text-zinc-600 text-center">Acknowledged</span>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Detail panel */}
        {detail && (
          <div className="w-80 bg-[#0c0c0f] border-l border-zinc-800/60 p-5 overflow-y-auto shrink-0">
            <h2 className="text-sm font-semibold text-zinc-50 mb-1">{detail.message}</h2>
            <span className={`inline-block text-[9px] font-semibold px-2.5 py-0.5 rounded mb-4 ${sevBadge(detail.severity)}`}>
              {detail.severity.toUpperCase()}
            </span>

            <Field label="Source" value={detail.camera_name} />
            <Field label="Model" value={detail.model_key} />
            <Field label="Status" value={detail.status} />
            <Field label="Timestamp" value={new Date(detail.created_at).toLocaleString()} />

            {detail.payload && Object.keys(detail.payload).length > 0 && (
              <div className="mt-4">
                <div className="text-[9px] text-zinc-600 uppercase tracking-wider mb-1">Payload</div>
                <pre className="bg-surface-alt border border-zinc-800 rounded-lg p-3 text-[10px] text-zinc-500 font-mono overflow-auto max-h-48 whitespace-pre-wrap">
                  {JSON.stringify(detail.payload, null, 2)}
                </pre>
              </div>
            )}

            {detail.status === "open" && (
              <div className="flex gap-2 mt-5">
                <button
                  onClick={() => handleAcknowledge(detail.id)}
                  className="flex-1 py-2 rounded-lg bg-blue-500/15 text-blue-400 text-[10px] font-semibold hover:bg-blue-500/25 transition-colors"
                >
                  Acknowledge
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

function Field({ label, value }) {
  return (
    <div className="mb-3">
      <div className="text-[9px] text-zinc-600 uppercase tracking-wider mb-0.5">{label}</div>
      <div className="text-xs text-zinc-400">{value}</div>
    </div>
  );
}

function sevColor(sev) {
  return { high: "bg-red-500", medium: "bg-amber-500", low: "bg-blue-500" }[sev] || "bg-zinc-600";
}
function sevBadge(sev) {
  return { high: "bg-red-500/15 text-red-400", medium: "bg-amber-500/12 text-amber-400", low: "bg-blue-500/10 text-blue-400" }[sev] || "";
}
function formatTime(iso) {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  return `${Math.round(diff / 3600)}h ago`;
}

function groupAlerts(alerts, mode) {
  const map = {};
  alerts.forEach((a) => {
    let key;
    if (mode === "severity") key = a.severity;
    else if (mode === "camera") key = a.camera_name || `Camera ${a.camera}`;
    else if (mode === "model") key = a.model_key;
    else {
      const diff = (Date.now() - new Date(a.created_at)) / 1000;
      if (diff < 60) key = "Last minute";
      else if (diff < 300) key = "Last 5 minutes";
      else if (diff < 3600) key = "Last hour";
      else key = "Older";
    }
    if (!map[key]) map[key] = [];
    map[key].push(a);
  });
  return Object.entries(map).map(([label, items]) => ({ label, items, count: items.length }));
}
```

- [ ] **Step 2: Update App.jsx import**

Replace AlertsPage placeholder with: `import AlertsPage from "./pages/AlertsPage";`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/AlertsPage.jsx frontend/src/App.jsx
git commit -m "feat: Alerts page with grouping, detail panel, acknowledge, and payload viewer"
```

---

### Task 12: Models page

**Files:**
- Create: `frontend/src/pages/ModelsPage.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Create ModelsPage**

`frontend/src/pages/ModelsPage.jsx`:

```jsx
import { useState, useEffect } from "react";
import { api } from "../api";
import Toggle from "../components/Toggle";

export default function ModelsPage() {
  const [models, setModels] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [overrides, setOverrides] = useState({});

  useEffect(() => {
    api.listModels().then((data) => setModels(data.results || data));
    api.listCameras().then((data) => {
      const cams = data.results || data;
      setCameras(cams);
      // Load overrides for each camera
      cams.forEach((cam) => {
        api.listCameraModels(cam.id).then((ov) => {
          setOverrides((prev) => ({ ...prev, [cam.id]: ov }));
        });
      });
    });
  }, []);

  async function toggleGlobal(key, current) {
    await api.updateModel(key, { enabled: !current });
    const data = await api.listModels();
    setModels(data.results || data);
  }

  async function toggleCameraModel(camId, modelKey, current) {
    await api.updateCameraModel(camId, modelKey, { enabled: !current });
    const ov = await api.listCameraModels(camId);
    setOverrides((prev) => ({ ...prev, [camId]: ov }));
  }

  function getOverride(camId, modelKey) {
    const ovs = overrides[camId] || [];
    const found = ovs.find((o) => o.model_key === modelKey);
    return found ? found.is_enabled : true;
  }

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Model Management</h1>
          <span className="text-xs text-zinc-600">
            {models.length} models &middot; {models.filter((m) => m.is_enabled).length} active
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
        {/* Global settings */}
        <h2 className="text-sm font-semibold text-zinc-50 mb-1">Global Model Settings</h2>
        <p className="text-[10px] text-zinc-600 mb-4">Toggle models on/off globally. Per-camera overrides below.</p>

        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-2.5 mb-8">
          {models.map((model) => (
            <div key={model.key} className="bg-surface-alt border border-zinc-800 rounded-lg p-3.5 hover:border-zinc-700 transition-colors">
              <div className="flex justify-between items-center mb-2.5">
                <span className="text-xs font-semibold text-zinc-100 capitalize">{model.display_name || model.key}</span>
                <span className={`text-[8px] font-semibold px-2 py-0.5 rounded border ${
                  model.is_enabled
                    ? "bg-green-500/10 text-green-400 border-green-500/20"
                    : "bg-zinc-800 text-zinc-500 border-zinc-700"
                }`}>
                  {model.is_enabled ? "Active" : "Disabled"}
                </span>
              </div>
              {model.description && (
                <p className="text-[10px] text-zinc-500 leading-relaxed mb-3">{model.description}</p>
              )}
              <Toggle enabled={model.is_enabled} onChange={() => toggleGlobal(model.key, model.is_enabled)} />
            </div>
          ))}
        </div>

        {/* Per-camera overrides */}
        <h2 className="text-sm font-semibold text-zinc-50 mb-1">Per-Camera Overrides</h2>
        <p className="text-[10px] text-zinc-600 mb-4">Override global settings for individual cameras.</p>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="text-left text-[9px] text-zinc-600 uppercase tracking-wider px-3 py-2 border-b border-zinc-800">Camera</th>
                {models.map((m) => (
                  <th key={m.key} className="text-center text-[9px] text-zinc-600 uppercase tracking-wider px-3 py-2 border-b border-zinc-800 capitalize">
                    {m.key}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cameras.map((cam) => (
                <tr key={cam.id}>
                  <td className="px-3 py-2 border-b border-zinc-800/50">
                    <div className="flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${cam.is_active ? "bg-green-500" : "bg-zinc-600"}`} />
                      <span className="text-[11px] text-zinc-400">{cam.name}</span>
                    </div>
                  </td>
                  {models.map((m) => (
                    <td key={m.key} className="text-center px-3 py-2 border-b border-zinc-800/50">
                      <div className="flex justify-center">
                        <Toggle
                          size="sm"
                          enabled={getOverride(cam.id, m.key)}
                          onChange={() => toggleCameraModel(cam.id, m.key, getOverride(cam.id, m.key))}
                        />
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
```

- [ ] **Step 2: Update App.jsx import**

Replace ModelsPage placeholder with: `import ModelsPage from "./pages/ModelsPage";`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ModelsPage.jsx frontend/src/App.jsx
git commit -m "feat: Models page with global toggles and per-camera override table"
```

---

### Task 13: Dev Lab page

**Files:**
- Create: `frontend/src/pages/DevLabPage.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Create DevLabPage**

`frontend/src/pages/DevLabPage.jsx`:

```jsx
import { useState, useEffect, useRef } from "react";
import { api } from "../api";

const TABS = ["Video Analysis", "Live Camera Test", "Threshold Tuning", "Performance"];

export default function DevLabPage() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Developer Lab</h1>
          <span className="text-xs text-zinc-600">Testing & debugging</span>
        </div>
      </div>

      <div className="flex border-b border-zinc-800/60 px-5 shrink-0">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(i)}
            className={`px-4 py-2.5 text-[11px] border-b-2 -mb-px transition-colors ${
              activeTab === i
                ? "text-blue-400 border-blue-500"
                : "text-zinc-600 border-transparent hover:text-zinc-400"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-hidden">
        {activeTab === 0 && <VideoAnalysis />}
        {activeTab === 1 && <LiveCameraTest />}
        {activeTab === 2 && <ThresholdTuning />}
        {activeTab === 3 && <PerformanceTab />}
      </div>
    </>
  );
}

function VideoAnalysis() {
  const [file, setFile] = useState(null);
  const [video, setVideo] = useState(null);
  const [results, setResults] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [config, setConfig] = useState({ sample_every_n_frames: 10, max_samples: 50 });
  const [previewMode, setPreviewMode] = useState("raw");
  const fileRef = useRef();

  function addLog(level, msg) {
    const ts = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { ts, level, msg }]);
  }

  async function handleUpload() {
    if (!file) return;
    addLog("info", `Uploading ${file.name} (${(file.size / 1024 / 1024).toFixed(1)}MB)`);
    const v = await api.uploadVideo(file);
    setVideo(v);
    addLog("ok", `Upload complete — ID: ${v.id}`);
  }

  async function handleAnalyze() {
    if (!video) return;
    setAnalyzing(true);
    addLog("info", `Analysis started — ${config.max_samples} samples @ every ${config.sample_every_n_frames} frames`);
    try {
      const r = await api.analyzeVideo(video.id, config);
      setResults(r);
      addLog("ok", `Analysis complete — ${r.frames_analyzed}/${r.frames_total} frames`);
    } catch (err) {
      addLog("err", `Analysis failed: ${err.message}`);
    }
    setAnalyzing(false);
  }

  return (
    <div className="flex h-full">
      {/* Left: Controls */}
      <div className="w-1/2 border-r border-zinc-800/60 p-4 overflow-y-auto space-y-5">
        <Section title="Upload Video">
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-zinc-800 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500/50 transition-colors"
          >
            <div className="text-2xl text-zinc-600 mb-2">&#128206;</div>
            <div className="text-[11px] text-zinc-500">{file ? file.name : "Drop video or click to browse"}</div>
            <div className="text-[9px] text-zinc-700 mt-1">MP4, AVI, MOV</div>
            <input ref={fileRef} type="file" accept="video/*" className="hidden" onChange={(e) => setFile(e.target.files[0])} />
          </div>
          {file && !video && (
            <button onClick={handleUpload} className="mt-2 w-full py-2 rounded-lg bg-blue-500/15 text-blue-400 text-[10px] font-semibold hover:bg-blue-500/25">
              Upload
            </button>
          )}
        </Section>

        {video && (
          <Section title="Analysis Configuration">
            <ConfigRow label="Sample every N frames" value={config.sample_every_n_frames} onChange={(v) => setConfig((c) => ({ ...c, sample_every_n_frames: parseInt(v) }))} />
            <ConfigRow label="Max samples" value={config.max_samples} onChange={(v) => setConfig((c) => ({ ...c, max_samples: parseInt(v) }))} />
            <button onClick={handleAnalyze} disabled={analyzing} className="mt-3 w-full py-2 rounded-lg bg-blue-500/15 text-blue-400 text-[10px] font-semibold hover:bg-blue-500/25 disabled:opacity-50">
              {analyzing ? "Analyzing..." : "Run Analysis"}
            </button>
          </Section>
        )}

        <Section title="Execution Log">
          <div className="bg-[#0c0c0f] border border-zinc-800/60 rounded-lg p-2.5 font-mono text-[9px] leading-relaxed max-h-40 overflow-y-auto">
            {logs.map((l, i) => (
              <div key={i}>
                <span className="text-zinc-700">[{l.ts}]</span>{" "}
                <span className={logColor(l.level)}>{l.level.toUpperCase()}</span>{" "}
                <span className="text-zinc-500">{l.msg}</span>
              </div>
            ))}
            {logs.length === 0 && <span className="text-zinc-700">Waiting for activity...</span>}
          </div>
        </Section>
      </div>

      {/* Right: Preview & Results */}
      <div className="w-1/2 p-4 overflow-y-auto space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-xs font-semibold text-zinc-100">Preview</h3>
          <div className="flex gap-1">
            {["raw", "annotated"].map((mode) => (
              <button
                key={mode}
                onClick={() => setPreviewMode(mode)}
                className={`px-2.5 py-1 rounded-md border text-[9px] capitalize ${
                  previewMode === mode
                    ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                    : "text-zinc-600 border-zinc-800"
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
        <div className="bg-surface-alt border border-zinc-800 rounded-lg aspect-video flex items-center justify-center overflow-hidden">
          {video ? (
            <img src={api.videoStreamUrl(video.id, previewMode === "annotated")} alt="Preview" className="w-full h-full object-contain" />
          ) : (
            <span className="text-[10px] text-zinc-700">Upload a video to preview</span>
          )}
        </div>

        {results && (
          <div className="bg-surface-alt border border-zinc-800 rounded-lg p-3.5">
            <h4 className="text-[11px] font-semibold text-zinc-100 mb-2">Detection Summary</h4>
            <ResultRow label="Frames analyzed" value={`${results.frames_analyzed} / ${results.frames_total}`} />
            {summarizeResults(results.results).map(({ key, count }) => (
              <ResultRow key={key} label={`${key} detections`} value={`${count}`} variant={count > 0 ? "danger" : "ok"} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function LiveCameraTest() {
  const [cameras, setCameras] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    api.listCameras().then((data) => setCameras(data.results || data));
  }, []);

  return (
    <div className="p-5 space-y-4">
      <Section title="Select Camera">
        <div className="flex gap-2 flex-wrap">
          {cameras.map((cam) => (
            <button
              key={cam.id}
              onClick={() => setSelectedId(cam.id)}
              className={`px-3 py-1.5 rounded-lg border text-[10px] ${
                selectedId === cam.id
                  ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                  : "text-zinc-500 border-zinc-800"
              }`}
            >
              {cam.name}
            </button>
          ))}
        </div>
      </Section>
      {selectedId && (
        <div className="bg-surface-alt border border-zinc-800 rounded-lg aspect-video overflow-hidden">
          <img src={api.cameraStreamUrl(selectedId, true)} alt="Live test" className="w-full h-full object-contain" />
        </div>
      )}
    </div>
  );
}

function ThresholdTuning() {
  const [thresholds, setThresholds] = useState(null);

  useEffect(() => {
    api.getThresholds().then(setThresholds);
  }, []);

  async function handleChange(key, value) {
    const updated = { ...thresholds, [key]: value };
    setThresholds(updated);
    await api.updateThresholds({ [key]: value });
  }

  if (!thresholds) return <div className="p-5 text-zinc-600 text-xs">Loading...</div>;

  return (
    <div className="p-5 max-w-lg space-y-5">
      <Section title="Detection Thresholds">
        <Slider label="Confidence threshold" value={thresholds.confidence} min={0} max={1} step={0.01} onChange={(v) => handleChange("confidence", v)} />
        <Slider label="Fatigue consecutive frames" value={thresholds.fatigue_consecutive_frames} min={1} max={30} step={1} onChange={(v) => handleChange("fatigue_consecutive_frames", v)} />
        <Slider label="EAR threshold" value={thresholds.ear_threshold} min={0} max={0.5} step={0.01} onChange={(v) => handleChange("ear_threshold", v)} />
        <Slider label="MAR threshold" value={thresholds.mar_threshold} min={0} max={1} step={0.01} onChange={(v) => handleChange("mar_threshold", v)} />
        <Slider label="Head tilt degrees" value={thresholds.head_tilt_degrees} min={5} max={45} step={0.5} onChange={(v) => handleChange("head_tilt_degrees", v)} />
      </Section>
    </div>
  );
}

function PerformanceTab() {
  const [perf, setPerf] = useState(null);

  useEffect(() => {
    loadPerf();
    const interval = setInterval(loadPerf, 2000);
    return () => clearInterval(interval);
  }, []);

  function loadPerf() {
    api.getPerformance().then(setPerf).catch(() => {});
  }

  if (!perf) return <div className="p-5 text-zinc-600 text-xs">Loading...</div>;

  return (
    <div className="p-5">
      <div className="grid grid-cols-2 gap-3 max-w-md">
        <PerfCard label="CPU Usage" value={`${perf.cpu_percent}%`} good={perf.cpu_percent < 80} />
        <PerfCard label="Memory" value={`${perf.memory_mb}MB`} good={perf.memory_mb < 4000} />
        <PerfCard label="GPU Available" value={perf.gpu_available ? "Yes" : "No"} good={perf.gpu_available} />
        <PerfCard label="GPU Usage" value={perf.gpu_percent >= 0 ? `${perf.gpu_percent}%` : "N/A"} good={perf.gpu_percent < 80} />
      </div>
    </div>
  );
}

// ---- Shared sub-components ----

function Section({ title, children }) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-zinc-100 mb-2.5">{title}</h3>
      {children}
    </div>
  );
}

function ConfigRow({ label, value, onChange }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
      <span className="text-[10px] text-zinc-400">{label}</span>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-20 text-center bg-surface-alt border border-zinc-800 rounded-md px-2 py-1 text-[10px] text-zinc-400 font-mono"
      />
    </div>
  );
}

function Slider({ label, value, min, max, step, onChange }) {
  return (
    <div className="py-2.5">
      <div className="flex justify-between text-[10px] mb-1.5">
        <span className="text-zinc-400">{label}</span>
        <span className="text-blue-400 font-mono">{typeof value === "number" ? value.toFixed(step < 1 ? 2 : 0) : value}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1 bg-zinc-800 rounded-full appearance-none cursor-pointer accent-blue-500"
      />
    </div>
  );
}

function ResultRow({ label, value, variant }) {
  const color = variant === "danger" ? "text-red-400" : variant === "ok" ? "text-green-400" : "text-zinc-400";
  return (
    <div className="flex justify-between py-1 text-[10px]">
      <span className="text-zinc-500">{label}</span>
      <span className={`font-mono ${color}`}>{value}</span>
    </div>
  );
}

function PerfCard({ label, value, good }) {
  return (
    <div className="bg-surface-alt border border-zinc-800 rounded-lg p-3 text-center">
      <div className={`text-xl font-bold font-mono ${good ? "text-green-400" : "text-amber-400"}`}>{value}</div>
      <div className="text-[9px] text-zinc-600 uppercase tracking-wider mt-0.5">{label}</div>
    </div>
  );
}

function logColor(level) {
  return { info: "text-blue-500", ok: "text-green-500", warn: "text-amber-500", err: "text-red-500" }[level] || "text-zinc-500";
}

function summarizeResults(results) {
  const counts = {};
  (results || []).forEach((frame) => {
    Object.entries(frame.detections || {}).forEach(([key, det]) => {
      if (det.detected || (det.payload?.missing_count > 0)) {
        counts[key] = (counts[key] || 0) + 1;
      }
    });
  });
  return Object.entries(counts).map(([key, count]) => ({ key, count }));
}
```

- [ ] **Step 2: Update App.jsx**

Replace DevLabPage placeholder with: `import DevLabPage from "./pages/DevLabPage";`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DevLabPage.jsx frontend/src/App.jsx
git commit -m "feat: Dev Lab page with video analysis, live test, threshold tuning, and performance tabs"
```

---

## Chunk 4: Integration + Final Wiring

### Task 14: Update App.jsx with all real page imports

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Final App.jsx**

Replace the file to import all real pages (removing inline placeholders). The structure from Task 8 stays, just swap imports:

```jsx
import FeedsPage from "./pages/FeedsPage";
import AlertsPage from "./pages/AlertsPage";
import ModelsPage from "./pages/ModelsPage";
import DevLabPage from "./pages/DevLabPage";
```

Remove the 4 inline placeholder functions.

- [ ] **Step 2: Build and verify**

Run: `cd frontend && npm run build`
Expected: Build succeeds, `dist/` updated

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: wire all page imports in App.jsx"
```

---

### Task 15: Update Dockerfile

**Files:**
- Modify: `Dockerfile`

- [ ] **Step 1: Update Dockerfile for Django**

Key changes:
- `WORKDIR /app/backend`
- Install frontend deps + build
- Collect static files
- Use `daphne` as entrypoint instead of `python backend/app.py`

```dockerfile
FROM continuumio/miniconda3

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 curl && \
    rm -rf /var/lib/apt/lists/*

# Install dlib via conda
RUN conda install -y -c conda-forge dlib

# Copy project
COPY . /app
WORKDIR /app

# Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Frontend build
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    cd frontend && npm ci && npm run build

# Django setup
WORKDIR /app/backend
RUN python manage.py collectstatic --noinput 2>/dev/null; true

# Uploads directory
RUN mkdir -p uploads/dev_videos && chmod -R 777 uploads

EXPOSE 7860

CMD ["daphne", "-b", "0.0.0.0", "-p", "7860", "sentinel.asgi:application"]
```

- [ ] **Step 2: Commit**

```bash
git add Dockerfile
git commit -m "refactor: update Dockerfile for Django + Daphne ASGI server"
```

---

### Task 16: Create Django superuser + verify full stack

- [ ] **Step 1: Run migrations**

```bash
cd backend
conda activate fatigue_env
python manage.py migrate
python manage.py createsuperuser --username admin --email admin@localhost
```

- [ ] **Step 2: Seed a test camera**

```bash
cd backend
python manage.py shell -c "
from cameras.models import Camera
Camera.objects.get_or_create(name='Webcam', source_url='0', defaults={'location': 'Local', 'is_active': True})
print('Camera created')
"
```

- [ ] **Step 3: Start backend**

```bash
cd backend && daphne -b 0.0.0.0 -p 7860 sentinel.asgi:application
```

- [ ] **Step 4: Start frontend dev server**

```bash
cd frontend && npm run dev
```

- [ ] **Step 5: Manual verification checklist**

Open `http://localhost:5173`:
- [ ] Icon rail visible with 4 icons
- [ ] Feeds page loads, shows camera(s)
- [ ] Navigate to Alerts — page renders
- [ ] Navigate to Models — toggles work
- [ ] Navigate to Dev Lab — tabs switch
- [ ] Open `http://localhost:7860/admin/` — Django admin accessible
- [ ] WebSocket connects (check browser console for no WS errors)

- [ ] **Step 6: Commit any fixes**

```bash
git add -A
git commit -m "feat: full stack integration verified — Django + React dashboard operational"
```
