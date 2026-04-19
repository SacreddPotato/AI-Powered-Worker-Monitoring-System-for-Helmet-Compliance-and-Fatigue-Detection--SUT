from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AlertViewSet,
    alert_severity_matrix_view,
    camera_alert_severity_view,
    apply_global_alert_severity_override_view,
)

router = DefaultRouter()
router.register(r'alerts', AlertViewSet)

urlpatterns = [
    path('alerts/severity/matrix/', alert_severity_matrix_view, name='alert-severity-matrix'),
    path('alerts/severity/cameras/<int:camera_id>/<str:model_key>/', camera_alert_severity_view, name='camera-alert-severity'),
    path('alerts/severity/apply-global/', apply_global_alert_severity_override_view, name='alerts-severity-apply-global'),
    path('', include(router.urls)),
]
