from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from users.models import UserProfile
import json
import jwt
import numpy as np
import asyncio

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

class TournamentPongConsumer(AsyncWebsocketConsumer):
	groups_info = {}
	tournaments = []

	async def connect(self):
		# JWT 에서 nick_name 추출
        token = self.scope['url_route']['kwargs']['token']
		self.my_pk_id = jwt.decode(token, settings.SECRET_KEY, algorithm='HS256')['intra_pk_id']
		self.nick_name = await TournamentPongConsumer.get_name(self.my_pk_id)

		# 빈 토너먼트 방에 참여
        self.tournament_group_name = f"tournament_{self.tournament_id}"

        # 채널에 추가
        await self.channel_layer.group_add(
            self.tournament_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 토너먼트 그룹에서 나가기
        await self.channel_layer.group_discard(
            self.tournament_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        # 클라이언트로부터의 메시지 처리

    async def send_game_updates(self, event):
        # 게임 업데이트 메시지를 클라이언트에게 전송
        await self.send(text_data=json.dumps(event))

	@database_sync_to_async
	def get_name(pk_id):
		return UserProfile.objects.get(intra_pk_id=pk_id).intra_id