
from django.urls import re_path

from . import consumers
from tournamentPong import TournamentPongConsumer

websocket_urlpatterns = [
    re_path('multiPong/', consumers.PongConsumer.as_asgi()),
    re_path('^tournamentPong/(?P<token>[\w-]*.[\w-]*.[\w-]+)/$', TournamentPongConsumer.as_asgi()),
]