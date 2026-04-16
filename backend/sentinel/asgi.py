import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinel.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from alerts.routing import websocket_urlpatterns as alert_ws
<<<<<<< HEAD
from cameras.routing import websocket_urlpatterns as camera_ws
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
from devlab.routing import websocket_urlpatterns as devlab_ws

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
<<<<<<< HEAD
    'websocket': URLRouter(alert_ws + camera_ws + devlab_ws),
=======
    'websocket': URLRouter(alert_ws + devlab_ws),
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
})
