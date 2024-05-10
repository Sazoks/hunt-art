import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

from apps.websockets.routing import websocket_urlpatterns


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

asgi_app = get_asgi_application()


application = ProtocolTypeRouter(
    {
        "http": asgi_app,
        "websocket": AllowedHostsOriginValidator(
            URLRouter(websocket_urlpatterns)
        ),
    }
)
