from django.urls import path
from .consumers import VideoAnalysisConsumer, WebcamAnalysisConsumer

websocket_urlpatterns = [
    path('ws/video-analysis/', VideoAnalysisConsumer.as_asgi()),
    path('ws/webcam-analysis/', WebcamAnalysisConsumer.as_asgi()),
]
