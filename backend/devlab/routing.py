from django.urls import path
from .consumers import VideoAnalysisConsumer

websocket_urlpatterns = [
    path('ws/video-analysis/', VideoAnalysisConsumer.as_asgi()),
]
