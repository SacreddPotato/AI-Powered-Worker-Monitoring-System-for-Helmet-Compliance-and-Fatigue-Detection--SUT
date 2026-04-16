from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModelSettingViewSet, DetectionViewSet, camera_models_view, camera_models_overrides_view, analyze_frame

router = DefaultRouter()
router.register(r'models', ModelSettingViewSet)
router.register(r'detections', DetectionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('cameras/models/overrides/', camera_models_overrides_view, name='camera-models-overrides'),
    path('cameras/<int:camera_id>/models/', camera_models_view, name='camera-models-list'),
    path('cameras/<int:camera_id>/models/<str:model_key>/', camera_models_view, name='camera-models-detail'),
    path('detections/analyze/', analyze_frame, name='analyze-frame'),
]
