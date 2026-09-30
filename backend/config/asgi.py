"""ASGI entrypoint with WebSocket and Django Channels support."""
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import notifications.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

# Imported after Django setup (it touches model imports lazily otherwise).
from config.ws_auth import JWTAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # Session auth first (AuthMiddlewareStack), then JWT (?token=/Authorization)
    # overrides it for SPA clients that hold no session cookie.
    "websocket": AuthMiddlewareStack(
        JWTAuthMiddleware(
            URLRouter(
                notifications.routing.websocket_urlpatterns
            )
        )
    ),
})
