
import json

class GameServer:

    config = dict()
    sessions = list()
    default_speed = float()

    def __init__(self, config_file_name):
        self.load_config(config_file_name)
        if 'defaultDogSpeed' in self.config.keys():
            self.default_speed = self.config['defaultDogSpeed']

    def load_config(self, config_file_name):
        try:
            f = open(config_file_name)
            self.config = json.load(f)
            return True
        except Exception as ex:
            print(ex)
            return False

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

    def action(self, token, direction):

        for session in self.sessions:
            session: GameSession
            for player in session.players:
                if player.token == token:
                    player.set_speed(direction, session.default_speed)
                    return True
        return False

    def tick(self, ticks):
        for session in self.sessions:
            session.tick(ticks)


class Dog:

    _id = int()
    token = None
    name = str()
    x, y = int(), int()


class Player:

    dog = Dog()

    speed = [0, 0]
    direction = 'U'

    def __init__(self, name, token, _id, x, y):
        self.name = name
        self.token = token
        self.id = _id
        self.x = x
        self.y = y

    def set_speed(self, direction, speed):

        if direction == 'L':
            self.speed = [-speed, 0]
        elif direction == 'U':
            self.speed = [0, speed]
        elif direction == 'R':
            self.speed = [speed, 0]
        elif direction == 'D':
            self.speed = [0, -speed]
        else:
            self.speed = [0, 0]
            return
        self.direction = direction

    def set_position(self, position):
        self.x, self.y = position

    def get_state(self):
        state = {
            'pos': [self.x, self.y],
            'speed': self.speed,
            'dir': self.direction
        }
        return state


class GameSession:

    map = dict()
    players = list()
    default_speed = float()

    def __init__(self, _map, default_speed):
        self.map = _map
        if 'DogSpeed' in self.map.keys():
            self.default_speed = self.map['DogSpeed']
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
            start_x, start_y = player.x, player.y
            stop_x = start_x + player.speed[0] * (ticks / 1000)
            stop_y = start_y + player.speed[1] * (ticks / 1000)
            start_point = (start_x, start_y)
            stop_point = (stop_x, stop_y)
            true_stop_point = self.bounded_move(start_point, stop_point)
            if true_stop_point != stop_point:
                player.set_speed('S', 0)
            player.set_position(true_stop_point)

    def bounded_move(self, start_point, stop_point):
        start_roads = list()    # Дороги, на которых стоит игрок в начале хода (может быть пересечение дорог)
        for road in self.map['roads']:
            if check_road_inclusion(road, start_point):
                start_roads.append(road)
        if len(start_roads) == 0:
            raise "Your glass if you are wrong"
        for road in start_roads:
            if check_road_inclusion(road, stop_point):
                return stop_point
        return bound_move(start_roads[0], stop_point)   # При очень длинных тиках (больше длины дороги)
                                                        # и старте с перекрёстка может вылезти баг


def bound_move(road, point, road_width=0.4):
    x0, y0 = (road['x0'], road['y0'])
    if 'x1' in road.keys():
        x1, y1 = (road['x1'], road['y0'])
    else:
        x1, y1 = (road['x0'], road['y1'])

    return bound(x0, x1, point[0]), bound(y0, y1, point[1], road_width)


def check_road_inclusion(road: dict, pose, road_width=0.4):
    x0, y0 = (road['x0'], road['y0'])

    if 'x1' in road.keys():
        # horizontal road
        x1, y1 = (road['x1'], road['y0'])
    else:
        # vertical road
        x1, y1 = (road['x0'], road['y1'])

    # check vertical inclusion
    if not min(y0, y1) - road_width < pose[1] < max(y0, y1) + road_width:
        return False

    # check left side
    if not min(x0, x1) - road_width < pose[0] < max(x0, x1) + road_width:
        return False

    return True


def bound(bound_1, bound_2, value, road_width=0.4):

    lower = min(bound_1, bound_2) - road_width
    upper = max(bound_1, bound_2) + road_width

    result = min(upper, value)
    result = max(lower, result)

    return result
