from __future__ import annotations

import json
import logging
import math
from typing import List, Optional
from dataclasses import dataclass

from pathlib import Path


from enum import Enum


class ErrorCodes(Enum):
    file_not_found = 100
    unable_to_load_json = 101


class Direction(Enum):
    U = 1
    R = 2
    D = 3
    L = 4

    def __str__(self):
        return self.name


@dataclass
class Point:
    x: float
    y: float

    def __le__(self, other: Point) -> bool:
        return self.x <= other.x and self.y <= other.y

    def __ge__(self, other: Point) -> bool:
        return self.x >= other.x and self.y >= other.y

    def __lt__(self, other: Point) -> bool:
        return self.x < other.x and self.y < other.y

    def __str__(self) -> str:
        return f'[{self.x}, {self.y}]'

    def __add__(self, other: Point) -> Point:
        x = self.x + other.x
        y = self.y + other.y
        return Point(x, y)

    @staticmethod
    def measure_distance(a: Point, b: Point) -> float:

        squared_distance = (b.x - a.x) ** 2 + (b.y - a.y) ** 2
        return math.sqrt(squared_distance)


class Vector2D(Point):

    def __mul__(self, other: float) -> Vector2D:
        x = self.x * other
        y = self.y * other
        return Vector2D(x, y)


class Road:

    def __init__(self, json_src: dict, width=0.4):

        x0, y0 = json_src['x0'], json_src['y0']
        if 'x1' in json_src.keys():
            # horizontal road
            x1, y1 = json_src['x1'], json_src['y0']
        else:
            # vertical
            x1, y1 = json_src['x0'], json_src['y1']

        left_bottom_x = min(x0, x1) - width
        left_bottom_y = min(y0, y1) - width
        right_top_x = max(x0, x1) + width
        right_top_y = max(y0, y1) + width

        self.left_bottom_corner = Point(left_bottom_x, left_bottom_y)
        self.right_top_corner = Point(right_top_x, right_top_y)

    def is_on_the_road(self, point: Point) -> bool:
        return self.left_bottom_corner <= point <= self.right_top_corner

    def bound_to_the_road(self, point: Point) -> Point:
        new_x = bound(self.left_bottom_corner.x, self.right_top_corner.x, point.x)
        new_y = bound(self.left_bottom_corner.y, self.right_top_corner.y, point.y)
        return Point(new_x, new_y)


@dataclass
class Player:

    name: str
    token: str
    id: int
    position: Point
    speed = Vector2D(0, 0)
    direction = Direction.U

    def set_speed(self, direction: str, speed: float):

        direction = Direction[direction]

        if direction == Direction.U:
            self.speed = Vector2D(0, speed)
        elif direction == Direction.R:
            self.speed = Vector2D(speed, 0)
        elif direction == Direction.D:
            self.speed = Vector2D(0, -speed)
        elif direction == Direction.L:
            self.speed = Vector2D(-speed, 0)
        else:
            self.speed = Vector2D(0, 0)
            return
        self.direction = direction

    def set_position(self, position: Point):
        self.position = position

    def get_state(self) -> Optional[dict]:
        state = {
            'pos': str(self.position),
            'speed': str(self.speed),
            'dir': str(self.direction)
        }
        return state

    def estimate_new_position(self, ticks: int) -> Point:
        new_position: Point = self.position + self.speed * (ticks / 1000)
        return new_position


class GameSession:

    map = dict()
    players: List[Player] = list()
    default_speed = float()
    roads: List[Road] = list()

    def __init__(self, game_map: dict, default_speed):
        self.map = game_map
        for r in game_map['roads']:
            road = Road(r)
            self.roads.append(road)

        self.default_speed = game_map.get('dogSpeed', default_speed)

    def add_player(self, name: str, token: str, _id: int, position: Point):
        player = Player(name, token, _id, position)
        self.players.append(player)

    def get_state(self) -> Optional[dict]:
        state = dict()
        for player in self.players:
            player_state = {
                player.id: player.get_state()
            }
            state.update(player_state)
        return state

    def tick(self, ticks: int):
        for player in self.players:
            estimated_new_position = player.estimate_new_position(ticks)
            new_position: Point = self.bounded_move(player.position, estimated_new_position)
            if new_position is not None:
                player.set_position(new_position)

    def bounded_move(self, start_point: Point, stop_point: Point) -> Optional[Point]:
        start_roads: List[Road] = list()

        for road in self.roads:
            if road.is_on_the_road(start_point):
                start_roads.append(road)

        if len(start_roads) == 0:
            logging.warning("Player is not on the road. Position: %s, Map: %s", str(start_point), self.map['id'])
            return None

        most_far: Point = start_roads[0].bound_to_the_road(stop_point)

        if len(start_roads) == 1:
            return most_far

        max_distance = Point.measure_distance(start_point, most_far)

        for i in range(1, len(start_roads)):
            pretender: Point = start_roads[i].bound_to_the_road(stop_point)
            distance = Point.measure_distance(start_point, pretender)
            if distance > max_distance:
                most_far = pretender
                max_distance = distance

        return most_far


class GameServer:

    config: dict
    sessions: List[GameSession] = list()
    default_speed: float

    def __init__(self, config_file_name: Path):  # pathlib
        try:
            f = open(config_file_name)
            self.config = json.load(f)
        except FileNotFoundError:
            logging.error("Config file is not found. Check the file location: %s", config_file_name)
            # Change on the pathlib notation

            exit(-100)    # Как лучше оформлять человекочитаемые коды завершения? Через dict? enum?

        except json.decoder.JSONDecodeError as ex:
            logging.error("Unable to load json config. Error: %s", ex.args[0])
            exit(-101)

        if 'defaultDogSpeed' in self.config.keys():
            self.default_speed = self.config['defaultDogSpeed']

    def get_maps(self) -> Optional[List[dict]]:
        try:
            map_list = list()
            for m in self.config['maps']:
                map_list.append({'id': m['id'], 'name': m['name']})
            return map_list
        except KeyError:
            logging.warning("Unable to get maps from the server")
            return list()

    def get_map(self, map_id: str) -> Optional[dict]:
        try:
            for m in self.config['maps']:
                # Стоит ли собрать карты в отдельное поле сервера, чтобы не иметь двух возможностей словить keyerror?
                # И в целом распарсить конфиг по полям класса на этапе инициализации, чтобы сразу их использовать?

                if m['id'] == map_id:
                    return m
        except KeyError:
            logging.warning("There is a problem with maps in config. Config: %s", json.dumps(self.config))
            return None

        logging.warning("There is no such map. Requested map id: %s, available maps: %s",
                        map_id, json.dumps(self.get_maps()))
        return None

    def join(self, username: str, map_id: str, token: str, player_id: int, position: Point) -> bool:

        for session in self.sessions:
            session: GameSession
            if session.map['id'] == map_id:
                session.add_player(username, token, player_id, position)
                return True

        _map = self.get_map(map_id)
        if _map is None:
            return False

        session = GameSession(_map, self.default_speed)
        session.add_player(username, token, player_id, position)
        self.sessions.append(session)
        return True

    def get_state(self, token: str) -> Optional[dict]:
        for session in self.sessions:
            session: GameSession
            for player in session.players:
                player: Player
                if player.token == token:
                    return session.get_state()
        return None

    def move(self, token: str, direction: str) -> bool:

        for session in self.sessions:
            session: GameSession
            for player in session.players:
                if player.token == token:
                    player.set_speed(direction, session.default_speed)
                    return True
        return False    # There is no such player

    def tick(self, ticks: int):
        for session in self.sessions:
            session.tick(ticks)


def bound(bound_1: float, bound_2: float, value: float) -> float:

    lower = min(bound_1, bound_2)
    upper = max(bound_1, bound_2)

    result = min(upper, value)
    result = max(lower, result)

    return result
