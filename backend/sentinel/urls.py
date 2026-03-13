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
