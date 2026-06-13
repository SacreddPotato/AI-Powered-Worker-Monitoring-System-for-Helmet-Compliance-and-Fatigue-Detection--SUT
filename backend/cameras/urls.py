from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CameraViewSet,
    camera_zones_view,
    camera_zone_detail_view,
    camera_zone_reset_view,
)

router = DefaultRouter()
router.register(r'cameras', CameraViewSet)

urlpatterns = [
    path('cameras/<int:camera_id>/zones/', camera_zones_view, name='camera-zones'),
    path('cameras/<int:camera_id>/zones/<int:zone_id>/', camera_zone_detail_view, name='camera-zone-detail'),
    path('cameras/<int:camera_id>/zones/<int:zone_id>/reset/', camera_zone_reset_view, name='camera-zone-reset'),
    path('', include(router.urls)),
]
