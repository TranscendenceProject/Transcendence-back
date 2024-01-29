
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path('pong/', consumers.PongConsumer.as_asgi()),
]