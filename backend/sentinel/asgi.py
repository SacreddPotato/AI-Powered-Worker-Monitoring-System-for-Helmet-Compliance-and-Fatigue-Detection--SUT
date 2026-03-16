import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinel.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from alerts.routing import websocket_urlpatterns as alert_ws
from cameras.routing import websocket_urlpatterns as camera_ws
from devlab.routing import websocket_urlpatterns as devlab_ws

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': URLRouter(alert_ws + camera_ws + devlab_ws),
})
