from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
import json
import numpy as np
import asyncio

class PongConsumer(AsyncWebsocketConsumer):
	channel_layer = get_channel_layer()
	channel_group = 'channel_group'
	groups = {}
	groups_info = {}
	max_group_size = 2

	end_score = 10

	sphere_radius = 0.04
	sphere_initial_speed = 0.03
	sphere_max_speed = 0.06

	bar_position = 2.5
	bar_width = 0.1
	bar_height = 0.08
	bar_depth = 0.7

	ground_height = 6.0
	ground_width = 5.0


	async def get_group_member_count(self, channel_name):
		for group_name, members in PongConsumer.groups.items():
			if channel_name in members:
				return len(members)
		return 0

	async def add_to_group(self, channel_name):
		for group_name, members in PongConsumer.groups.items():
			if len(members) < PongConsumer.max_group_size:
				await PongConsumer.channel_layer.group_add(PongConsumer.channel_group, channel_name)
				members.append(channel_name)
				return group_name
		new_group_name = f"group_{len(PongConsumer.groups) + 1}"
		await PongConsumer.channel_layer.group_add(PongConsumer.channel_group, channel_name)
		PongConsumer.groups[new_group_name] = [channel_name]
		return new_group_name

	async def initialize_group(self):
		tmp_vector = np.array([1.0, 0.0, 1.0])
		sphere_direction = tmp_vector / np.linalg.norm(tmp_vector)
		PongConsumer.groups_info[self.my_group] = {
			'task': None,

			'sphere_direction': [sphere_direction[0], sphere_direction[1], sphere_direction[2]],

			'sphere_position': [0.0, 0.0, 0.0],

			'sphere_speed': PongConsumer.sphere_initial_speed,

			'player_1_score': 0,
			'player_2_score': 0,

			'p1_bar_position': [-PongConsumer.bar_position, 0.0, 0.0],

			'p2_bar_position': [PongConsumer.bar_position, 0.0, 0.0],

			'p1_moving_up': False,

			'p1_moving_down': False,

			'p2_moving_up': False,

			'p2_moving_down': False,

			'sphere_bounding_box': {
				'x_min': -PongConsumer.sphere_radius,
				'x_max': PongConsumer.sphere_radius,
				'y_min': -PongConsumer.sphere_radius,
				'y_max': PongConsumer.sphere_radius,
				'z_min': -PongConsumer.sphere_radius,
				'z_max': PongConsumer.sphere_radius
			},

			'p2_bar_box' : {
				'x_min': PongConsumer.bar_position - PongConsumer.bar_width / 2,
				'x_max': PongConsumer.bar_position + PongConsumer.bar_width / 2,
				'y_min': -PongConsumer.bar_height / 2,
				'y_max': PongConsumer.bar_height / 2,
				'z_min': -PongConsumer.bar_depth / 2,
				'z_max': PongConsumer.bar_depth / 2
			},

			'p1_bar_box' : {
				'x_min': -PongConsumer.bar_position - PongConsumer.bar_width / 2,
				'x_max': -PongConsumer.bar_position + PongConsumer.bar_width / 2,
				'y_min': -PongConsumer.bar_height / 2,
				'y_max': PongConsumer.bar_height / 2,
				'z_min': -PongConsumer.bar_depth / 2,
				'z_max': PongConsumer.bar_depth / 2
			},

			'upper_plane_normal': [-1.0, 0.0, 0.0],

			'upper_plane_constant': -PongConsumer.ground_height / 2.0,

			'lower_plane_normal': [1.0, 0.0, 0.0],

			'lower_plane_constant': -PongConsumer.ground_height / 2.0,

			'left_plane_normal': [0.0, 0.0, -1.0],

			'left_plane_constant': -PongConsumer.ground_width / 2.0,

			'right_plane_normal': [0.0, 0.0, 1.0],

			'right_plane_constant': -PongConsumer.ground_width / 2.0,
		}

	async def check_box_plane_collision(self, box_coordinates, plane_normal, plane_constant):
		min, max = 0, 0

		if plane_normal[0] > 0:
			min = plane_normal[0] * box_coordinates['x_min']
			max = plane_normal[0] * box_coordinates['x_max']
		
		else:
			min = plane_normal[0] * box_coordinates['x_max']
			max = plane_normal[0] * box_coordinates['x_min']
		
		if plane_normal[1] > 0:
			min += plane_normal[1] * box_coordinates['y_min']
			max += plane_normal[1] * box_coordinates['y_max']
		
		else:
			min += plane_normal[1] * box_coordinates['y_max']
			max += plane_normal[1] * box_coordinates['y_min']

		if plane_normal[2] > 0:
			min += plane_normal[2] * box_coordinates['z_min']
			max += plane_normal[2] * box_coordinates['z_max']

		else:
			min += plane_normal[2] * box_coordinates['z_max']
			max += plane_normal[2] * box_coordinates['z_min']

		return min <= -plane_constant and max >= -plane_constant

	async def check_box_bar_collision(self, box1_coordinates, box2_coordinates):
		return not (box1_coordinates['x_max'] < box2_coordinates['x_min'] or
				box1_coordinates['x_min'] > box2_coordinates['x_max'] or
				box1_coordinates['y_max'] < box2_coordinates['y_min'] or
				box1_coordinates['y_min'] > box2_coordinates['y_max'] or
				box1_coordinates['z_max'] < box2_coordinates['z_min'] or
				box1_coordinates['z_min'] > box2_coordinates['z_max'])

	async def reflect_vector(self, vector, normal):
		vector = np.array(vector)
		normal = np.array(normal)
		return vector - 2 * np.dot(vector, normal) * normal

	async def reflect_vector_from_bar(self, sphere_position, normal, bar_position):
		tmp_vector = np.array([0, 0, 0])
		position = np.array([sphere_position[0], sphere_position[1], sphere_position[2]])
		b_position = np.array([bar_position[0], bar_position[1], bar_position[2]])
		tmp_vector = (position - b_position) * 2 + normal
		return tmp_vector / np.linalg.norm(tmp_vector)

	async def moving_sphere(self):
		PongConsumer.groups_info[self.my_group]['sphere_position'][0] += PongConsumer.groups_info[self.my_group]['sphere_direction'][0] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		PongConsumer.groups_info[self.my_group]['sphere_position'][1] += PongConsumer.groups_info[self.my_group]['sphere_direction'][1] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		PongConsumer.groups_info[self.my_group]['sphere_position'][2] += PongConsumer.groups_info[self.my_group]['sphere_direction'][2] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		PongConsumer.groups_info[self.my_group]['sphere_bounding_box']['x_min'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][0] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		PongConsumer.groups_info[self.my_group]['sphere_bounding_box']['x_max'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][0] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		PongConsumer.groups_info[self.my_group]['sphere_bounding_box']['y_min'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][1] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		PongConsumer.groups_info[self.my_group]['sphere_bounding_box']['y_max'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][1] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		PongConsumer.groups_info[self.my_group]['sphere_bounding_box']['z_min'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][2] * PongConsumer.groups_info[self.my_group]['sphere_speed']
		PongConsumer.groups_info[self.my_group]['sphere_bounding_box']['z_max'] += PongConsumer.groups_info[self.my_group]['sphere_direction'][2] * PongConsumer.groups_info[self.my_group]['sphere_speed']

	async def initialize_sphere(self):
		PongConsumer.groups_info[self.my_group]['sphere_position'][0] = 0.0
		PongConsumer.groups_info[self.my_group]['sphere_position'][1] = 0.0
		PongConsumer.groups_info[self.my_group]['sphere_position'][2] = 0.0
		PongConsumer.groups_info[self.my_group]['sphere_bounding_box'] = {
			'x_min': -PongConsumer.sphere_radius,
			'x_max': PongConsumer.sphere_radius,
			'y_min': -PongConsumer.sphere_radius,
			'y_max': PongConsumer.sphere_radius,
			'z_min': -PongConsumer.sphere_radius,
			'z_max': PongConsumer.sphere_radius
		}
		PongConsumer.groups_info[self.my_group]['sphere_speed'] = PongConsumer.sphere_initial_speed

	async def check_sphere_collision(self):
		if await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['upper_plane_normal'], PongConsumer.groups_info[self.my_group]['upper_plane_constant']):
			PongConsumer.groups_info[self.my_group]['player_2_score'] += 1
			await self.initialize_sphere()
			await PongConsumer.channel_layer.group_send(
				PongConsumer.channel_group,
				{
					'type': 'send_scores',
					'users': PongConsumer.groups[self.my_group],
					'player_1_score': PongConsumer.groups_info[self.my_group]['player_1_score'],
					'player_2_score': PongConsumer.groups_info[self.my_group]['player_2_score'],
				}
			)
			if PongConsumer.groups_info[self.my_group]['player_2_score'] >= PongConsumer.end_score:
				await PongConsumer.channel_layer.group_send(
					PongConsumer.channel_group,
					{
						'type': 'send_game_over_disconnected',
						'users': PongConsumer.groups[self.my_group],
						'detail': 'game_over',
						'winner': 2
					}
				)
			await asyncio.sleep(1)

		elif await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['lower_plane_normal'], PongConsumer.groups_info[self.my_group]['lower_plane_constant']):
			PongConsumer.groups_info[self.my_group]['player_1_score'] += 1
			await self.initialize_sphere()
			await PongConsumer.channel_layer.group_send(
				PongConsumer.channel_group,
				{
					'type': 'send_scores',
					'users': PongConsumer.groups[self.my_group],
					'player_1_score': PongConsumer.groups_info[self.my_group]['player_1_score'],
					'player_2_score': PongConsumer.groups_info[self.my_group]['player_2_score'],
				}
			)
			if PongConsumer.groups_info[self.my_group]['player_1_score'] >= PongConsumer.end_score:
				await PongConsumer.channel_layer.group_send(
					PongConsumer.channel_group,
					{
						'type': 'send_game_over_disconnected',
						'users': PongConsumer.groups[self.my_group],
						'detail': 'game_over',
						'winner': 1
					}
				)
			await asyncio.sleep(1)

		elif await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['left_plane_normal'], PongConsumer.groups_info[self.my_group]['left_plane_constant']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector(PongConsumer.groups_info[self.my_group]['sphere_direction'], PongConsumer.groups_info[self.my_group]['left_plane_normal'])

		elif await self.check_box_plane_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['right_plane_normal'], PongConsumer.groups_info[self.my_group]['right_plane_constant']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector(PongConsumer.groups_info[self.my_group]['sphere_direction'], PongConsumer.groups_info[self.my_group]['left_plane_normal'])

		elif await self.check_box_bar_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['p1_bar_box']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector_from_bar(PongConsumer.groups_info[self.my_group]['sphere_position'], np.array([1, 0, 0]), PongConsumer.groups_info[self.my_group]['p1_bar_position'])
			if PongConsumer.groups_info[self.my_group]['sphere_speed'] < PongConsumer.sphere_max_speed:
				PongConsumer.groups_info[self.my_group]['sphere_speed'] += 0.005

		elif await self.check_box_bar_collision(PongConsumer.groups_info[self.my_group]['sphere_bounding_box'], PongConsumer.groups_info[self.my_group]['p2_bar_box']):
			PongConsumer.groups_info[self.my_group]['sphere_direction'] = await self.reflect_vector_from_bar(PongConsumer.groups_info[self.my_group]['sphere_position'], np.array([-1, 0, 0]), PongConsumer.groups_info[self.my_group]['p2_bar_position'])
			if PongConsumer.groups_info[self.my_group]['sphere_speed'] < PongConsumer.sphere_max_speed:
				PongConsumer.groups_info[self.my_group]['sphere_speed'] += 0.005

	async def moving_bar_bounding_box(self, box_coordinates, speed):
		box_coordinates['z_min'] += speed
		box_coordinates['z_max'] += speed

	async def main_loop(self):
		while True:
			await self.check_sphere_collision()
			await self.moving_sphere()
			await PongConsumer.channel_layer.group_send(
			    PongConsumer.channel_group,
			    {
			        'type': 'send_positions',
					'users': PongConsumer.groups[self.my_group],
			        'sphere_position': PongConsumer.groups_info[self.my_group]['sphere_position'],
			        'p1_bar_position': PongConsumer.groups_info[self.my_group]['p1_bar_position'],
			        'p2_bar_position': PongConsumer.groups_info[self.my_group]['p2_bar_position'],
			    }
			)
			await asyncio.sleep(0.01)

	async def send_scores(self, event):
		users = event['users']
		player_1_score = event['player_1_score']
		player_2_score = event['player_2_score']
		if self.channel_name in users:
			await self.send(text_data=json.dumps({
				'type': 'scores',
				'player_1_score': player_1_score,
				'player_2_score': player_2_score,
			}))

	async def send_positions(self, event):
		users = event['users']
		sphere_position = event['sphere_position']
		p1_bar_position = event['p1_bar_position']
		p2_bar_position = event['p2_bar_position']
		if self.channel_name in users:
			await self.send(text_data=json.dumps({
				'type': 'positions',
				'sphere_position': sphere_position,
				'p1_bar_position': p1_bar_position,
				'p2_bar_position': p2_bar_position,
			}))

	async def send_disconnect_message(self, event):
		users = event['users']
		if self.channel_name in users:
			await self.send(text_data=json.dumps({
				'type': 'disconnect_message',
			}))

	async def send_game_over_disconnected(self, event):
		users = event['users']
		detail = event['detail']
		winner = event['winner']
		if self.channel_name in users:
			await self.send(text_data=json.dumps({
				'type': 'game_over_disconnected',
				'winner': winner,
				'detail': detail
			}))

	async def connect(self):
		await self.accept()
		self.my_group = await self.add_to_group(self.channel_name)
		my_group_member_count = await self.get_group_member_count(self.channel_name)
		if my_group_member_count == 1:
			self.player_num = 1
			await self.send(text_data=json.dumps({
				'type': 'player_num',
				'player_num': 1
			}))
		elif my_group_member_count == 2:
			self.player_num = 2
			await self.send(text_data=json.dumps({
				'type': 'player_num',
				'player_num': 2
			}))
			await self.initialize_group()
			PongConsumer.groups_info[self.my_group]['task'] = asyncio.create_task(self.main_loop())

	async def disconnect(self, close_code):
		if self.my_group in PongConsumer.groups:
			PongConsumer.groups_info[self.my_group]['task'].cancel()
		if self.channel_name in PongConsumer.groups[self.my_group]:
			PongConsumer.groups[self.my_group].remove(self.channel_name)
		if (self.my_group in PongConsumer.groups_info and 
			PongConsumer.groups_info[self.my_group]['player_1_score'] < PongConsumer.end_score and 
			PongConsumer.groups_info[self.my_group]['player_2_score'] < PongConsumer.end_score):
			await self.channel_layer.group_send(
				PongConsumer.channel_group,
				{
					'type': 'send_game_over_disconnected',
					'users': PongConsumer.groups[self.my_group],
					'winner': 3 - self.player_num,
					'detail': 'game_over_disconnected'
				}
			)
		await PongConsumer.channel_layer.group_discard(PongConsumer.channel_group, self.channel_name)
		if self.my_group in PongConsumer.groups and len(PongConsumer.groups[self.my_group]) == 0:
			del PongConsumer.groups[self.my_group]
			del PongConsumer.groups_info[self.my_group]
		
	async def handle_keydown(self, data):
		player_key = f"p{data['player_num']}_bar"
		position_key = f"{player_key}_position"
		box_key = f"{player_key}_box"
		direction = 0.05 if data['keycode'] == 'ArrowRight' else -0.05 if data['keycode'] == 'ArrowLeft' else 0

		if direction != 0 and not await self.check_box_plane_collision(
			PongConsumer.groups_info[self.my_group][box_key],
			PongConsumer.groups_info[self.my_group][f"{'right' if direction > 0 else 'left'}_plane_normal"],
			PongConsumer.groups_info[self.my_group][f"{'right' if direction > 0 else 'left'}_plane_constant"]
		):
			PongConsumer.groups_info[self.my_group][position_key][2] += direction
			await self.moving_bar_bounding_box(PongConsumer.groups_info[self.my_group][box_key], direction)

	async def receive(self, text_data):
		data = json.loads(text_data)

		if data['type'] == 'keydown':
			if self.my_group in PongConsumer.groups_info:
				await self.handle_keydown(data)
