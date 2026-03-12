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
