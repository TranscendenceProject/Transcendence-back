"""
ASGI config for multi_pong project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pikaPong.settings')
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

import game.routing

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "https": django_asgi_app,

    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(game.routing.websocket_urlpatterns)
        )
    ),
})