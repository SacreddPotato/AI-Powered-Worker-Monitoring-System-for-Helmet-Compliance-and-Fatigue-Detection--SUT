from django.urls import path
from .consumers import CameraStreamConsumer

websocket_urlpatterns = [
    path('ws/cameras/<int:camera_id>/stream/', CameraStreamConsumer.as_asgi()),
]
