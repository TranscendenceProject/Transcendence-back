from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from users.models import UserProfile
import json
import jwt
import numpy as np
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from itertools import count

MAX_GROUP_SIZE = 2
MAX_TOURNAMENT_SIZE = 4

END_SCORE = 10

SPHERE_RADIUS = 0.04
SPHERE_INITIAL_SPEED = 0.03
SPHERE_MAX_SPEED = 0.06

BAR_POSITION = 2.5
BAR_WIDTH = 0.1
BAR_HEIGHT = 0.08
BAR_DEPTH = 0.7

GROUND_HEIGHT = 6.0
GROUND_WIDTH = 5.0

@dataclass
class Tournament:
    id: int = field(default_factory=count().__next__, init=False)
    name: Optional[str] = field(default=None, init=False)
    players: list[UserProfile] = field(default_factory=list)

    def __post_init__(self):
        self.name = f'tournament-{self.id}'

class TournamentPongConsumer(AsyncWebsocketConsumer):
	groups_info = {}
	tournaments = []

	async def connect(self):
		# JWT 에서 nick_name 추출
        token = self.scope['url_route']['kwargs']['token']
		pk_id = jwt.decode(token, settings.SECRET_KEY, algorithm='HS256')['intra_pk_id']
		self.user = await UserProfile.objects.aget(intra_pk_id=pk_id)

		# 토너먼트 방에 참여 TODO: tournaments 중에 이미 본인유저가 있으면 그 방에 다시 조인(재접속 관련)
        self.tournament = None
        for i, tournament in enumerate(TournamentPongConsumer.tournaments):
            # 4명 안 찬 방 있으면 그곳으로 조인
            if len(tournament.players) is not 4:
                tournament.players.append(self.user)
                self.tournament = tournament
                break
        # 빈 토너먼트 할당 못 받았으면(다 풀방이면) 새 토너먼트 개설
        if self.tournament is None:
            self.tournament = Tournament(players=[self.user])
            TournamentPongConsumer.tournaments.append(self.tournament)

        # 채널에 추가
        await self.channel_layer.group_add(
            self.tournament.name,
            self.channel_name
        )

        await self.accept()

        # TODO: 해당 채널 그룹에 방에 입장했다고 브로드캐스팅

    async def disconnect(self, close_code):
        # 토너먼트 그룹에서 나가기 TODO: tournaments 안에 있는 중복된 본인 디스컨넥션 필요?
        await self.channel_layer.group_discard(
            self.tournament.name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        # 클라이언트로부터의 메시지 처리

    async def send_game_updates(self, event):
        # 게임 업데이트 메시지를 클라이언트에게 전송
        await self.send(text_data=json.dumps(event))