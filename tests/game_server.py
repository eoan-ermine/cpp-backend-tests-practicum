
import json
import math
from typing import List
from dataclasses import field, dataclass

from enum import Enum


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

    def __le__(self, other):
        other: Point
        if self.x <= other.x and self.y <= other.y:
            return True
        else:
            return False

    def __ge__(self, other):
        other: Point

        if self.x >= other.x and self.y >= other.y:
            return True
        else:
            return False

    def __lt__(self, other):
        other: Point
        if self.x < other.x and self.y < other.y:
            return True
        else:
            return False

    def __str__(self):
        return f'[{self.x}, {self.y}]'

    def __add__(self, other):
        other: Point
        x = self.x + other.x
        y = self.y + other.y
        return Point(x, y)

    @staticmethod
    def measure_distance(a, b):
        a: Point
        b: Point

        distance_sqr = (b.x - a.x) ** 2 + (b.y - a.y) ** 2
        return math.sqrt(distance_sqr)


class Vector2(Point):

    def __mul__(self, other: float):
        x = self.x * other
        y = self.y * other
        return Vector2(x, y)


class Road:

    left_bottom_corner: Point
    right_top_corner: Point

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

    def is_on_the_road(self, point) -> bool:
        point: Point

        if self.left_bottom_corner <= point <= self.right_top_corner:
            return True
        else:
            return False

    def bound_to_the_road(self, point) -> Point:
        point: Point
        new_x = bound(self.left_bottom_corner.x, self.right_top_corner.x, point.x)
        new_y = bound(self.left_bottom_corner.y, self.right_top_corner.y, point.y)

        return Point(new_x, new_y)


@dataclass
class Player:

    name: str
    token: str
    id: int
    x: float
    y: float
    position: Point = field(init=False)
    speed = Vector2(0, 0)
    direction = Direction.U

    # def __init__(self, name, token, _id, x, y):
    #     pass

    def __post_init__(self):
        self.position = Point(self.x, self.y)
        self.direction = Direction.U
        del(self.x, self.y)                     # Is it a good practice?

    def set_speed(self, direction, speed):

        direction = Direction[direction]

        if direction == Direction.U:
            self.speed = Vector2(0, speed)
        elif direction == Direction.R:
            self.speed = Vector2(speed, 0)
        elif direction == Direction.D:
            self.speed = Vector2(0, -speed)
        elif direction == Direction.L:
            self.speed = Vector2(-speed, 0)
        else:
            self.speed = Vector2(0, 0)
            return
        self.direction = direction

    def set_position(self, position):
        self.position = position

    def get_state(self):
        state = {
            'pos': str(self.position),
            'speed': str(self.speed),
            'dir': str(self.direction)
        }
        return state

    def estimate_new_position(self, ticks: int):
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

        if 'dogSpeed' in game_map.keys():
            self.default_speed = game_map['dogSpeed']
        else:
            self.default_speed = default_speed

    def add_player(self, name, token, _id, x, y):
        player = Player(name, token, _id, x, y)
        self.players.append(player)

    def get_state(self):
        state = dict()
        for player in self.players:
            player_state = {
                player.id: player.get_state()
            }
            state.update(player_state)
        return state

    def tick(self, ticks):
        for player in self.players:
            estimated_new_position = player.estimate_new_position(ticks)
            new_position: Point = self.bounded_move(player.position, estimated_new_position)
            player.position = new_position

    def bounded_move(self, start_point: Point, stop_point: Point):

        start_roads = list()
        for road in self.roads:
            if road.is_on_the_road(start_point):
                start_roads.append(road)

        if len(start_roads) == 0:
            raise "Your glass if you are wrong"

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

    def __init__(self, config_file_name):
        try:
            f = open(config_file_name)
            self.config = json.load(f)
        except Exception as ex:
            print(ex)
            exit(-1)

        if 'defaultDogSpeed' in self.config.keys():
            self.default_speed = self.config['defaultDogSpeed']

    def get_maps(self):
        try:
            map_list = []
            for m in self.config['maps']:
                map_list.append({'id': m['id'], 'name': m['name']})
            return map_list
        except KeyError:
            print("There is no maps")
            return list()

    def get_map(self, map_id):
        try:
            for m in self.config['maps']:
                if m['id'] == map_id:
                    return m
        except KeyError:
            print("There is no maps")

        print("There is no such map")
        return None
        # return dict()

    def join(self, username, map_id, token, player_id, x, y):

        for session in self.sessions:
            session: GameSession
            if session.map['id'] == map_id:
                session.add_player(username, token, player_id, x, y)
                return True

        _map = self.get_map(map_id)
        if _map is None:
            # There is no such map
            return False

        session = GameSession(_map, self.default_speed)
        session.add_player(username, token, player_id, x, y)
        self.sessions.append(session)
        return True

    def get_state(self, token):
        for session in self.sessions:
            session: GameSession
            for player in session.players:
                player: Player
                if player.token == token:
                    return session.get_state()
        return False

    def move(self, token, direction):

        for session in self.sessions:
            session: GameSession
            for player in session.players:
                if player.token == token:
                    player.set_speed(direction, session.default_speed)
                    return True
        return False    # There is no such player

    def tick(self, ticks):
        for session in self.sessions:
            session.tick(ticks)


def bound(bound_1, bound_2, value):

    lower = min(bound_1, bound_2)
    upper = max(bound_1, bound_2)

    result = min(upper, value)
    result = max(lower, result)

    return result
