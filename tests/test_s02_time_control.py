import random
import time

import pytest
import requests
import game_server as game
from game_server import Point
import pathlib


@pytest.fixture()
def game_server():
    yield game.GameServer(pathlib.Path('/home/alex/YaPracticum/cpp-backend-tests-practicum/tests/data/config.json'))


def tick_server(server, delta):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}
    data = {"timeDelta": delta}
    res = server.request('POST', header, request, json=data)


def get_maps(server):
    request = 'api/v1/maps'
    res = server.get(request)
    return res.json()


def get_map(server, map_id):
    request = 'api/v1/maps/' + map_id
    res = server.get(request)
    return res.json()


def get_state(server, token):
    request = '/api/v1/game/state'
    header = {'content-type': 'application/json', 'Authorization': f'Bearer {token}'}
    res = server.request('GET', header, request)
    return res.json()


def get_player_state(server, token, player_id):
    state: dict = get_state(server, token)
    players: dict = state.get('players')
    player_state = players.get(str(player_id))
    return player_state


def get_parsed_state(server, token, player_id):
    state: dict = get_player_state(server, token, player_id)
    pos = state.get('pos')
    speed = state.get('speed')
    direction = state.get('dir')
    return pos, speed, direction


def move_player(server, token, direction: str):
    request = '/api/v1/game/player/action'
    header = {'content-type': 'application/json',  'Authorization': f'Bearer {token}'}
    data = {"move": direction}
    return server.request('POST', header, request, json=data)


def move_players(server, game_server: game.GameServer, token, direction):
    move_player(server, token, direction)
    game_server.move(token, direction)


def tick_both(server, game_server: game.GameServer, ticks):
    tick_server(server, ticks)
    game_server.tick(ticks)


def join_to_map(server, user_name, map_id):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": user_name, "mapId": map_id}
    return server.request('POST', header, request, json=data)


def test_tick_miss_delta(server):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}
    res = server.request('POST', header, request)

    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'
    assert res_json.get('message')


@pytest.mark.parametrize('delta', {0.0, '0', True})
def test_tick_invalid_type_delta(server, delta):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}

    data = {"timeDelta": delta}
    res = server.request('POST', header, request, json=data)

    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'
    assert res_json.get('message')


@pytest.mark.parametrize('method', ['GET', 'OPTIONS', 'HEAD', 'PUT', 'PATCH', 'DELETE'])
def test_tick_invalid_verb(server, method):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}
    res = server.request(method, header, request)
    print(res.headers)
    assert res.status_code == 405
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'

    if method != 'HEAD':
        res_json = res.json()
        assert res_json['code'] == 'invalidMethod'
        assert res_json.get('message')


@pytest.mark.randomize(min_num=0, max_num=10000, ncalls=10)
def test_tick_success(server, delta: int):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}
    data = {"timeDelta": delta}
    res = server.request('POST', header, request, json=data)

    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'

    res_json = res.json()
    print(res_json)
    assert res_json == dict()


def test_match_roads(server, game_server):

    py_maps = game_server.get_maps()
    server_maps = get_maps(server)

    assert py_maps == server_maps
    print(py_maps)

    for i in range(0, len(py_maps)):

        py_map = game_server.get_map(py_maps[i]['id'])
        if 'dogSpeed' in py_map.keys():
            py_map.pop('dogSpeed')
        server_map = get_map(server, server_maps[i]['id'])
        assert py_map == server_map


@pytest.mark.parametrize('direction', ['R', 'L', 'U', 'D'])
def test_turn_one_player(server_one_test, game_server, direction):
    name = 'name'
    map_id = 'map1'

    params: dict = join_to_map(server_one_test, name, map_id).json()
    token = params['authToken']
    player_id = params['playerId']

    position, _, _ = get_parsed_state(server_one_test, token, player_id)
    game_server.join(name, map_id, token, player_id, position)

    move_player(server_one_test, token, direction)
    game_server.move(token, direction)

    py_state = game_server.get_state(token)
    state = get_state(server_one_test, token)

    assert py_state == state


@pytest.mark.randomize(min_num=0, max_num=250, ncalls=5)
@pytest.mark.parametrize('map_id', ['map1', 'town'])
@pytest.mark.parametrize('direction', ['R', 'L', 'U', 'D'])
def test_small_move_one_player(server_one_test, game_server, direction, ticks: int, map_id):
    name = 'name'

    params: dict = join_to_map(server_one_test, name, map_id).json()
    token = params['authToken']
    player_id = params['playerId']

    position, _, _ = get_parsed_state(server_one_test, token, player_id)
    game_server.join(name, map_id, token, player_id, Point(position[0], position[1]))

    move_player(server_one_test, token, direction)
    game_server.move(token, direction)

    py_state = game_server.get_state(token)
    state = get_state(server_one_test, token)

    assert py_state == state

    tick_server(server_one_test, ticks)
    game_server.tick(ticks)

    py_state = game_server.get_state(token)
    state = get_state(server_one_test, token)
    print(py_state)
    print(state)

    assert py_state == state


@pytest.mark.randomize(min_num=1000, max_num=100000, ncalls=5)
@pytest.mark.parametrize('map_id', ['map1', 'town'])
@pytest.mark.parametrize('direction', ['R', 'L', 'U', 'D'])
def test_big_move_one_player(server_one_test, game_server, direction, ticks: int, map_id):
    name = 'name'
    # map_id = 'map1'

    params: dict = join_to_map(server_one_test, name, map_id).json()
    token = params['authToken']
    player_id = params['playerId']

    position, _, _ = get_parsed_state(server_one_test, token, player_id)
    game_server.join(name, map_id, token, player_id, Point(position[0], position[1]))

    move_player(server_one_test, token, direction)
    game_server.move(token, direction)

    py_state = game_server.get_state(token)
    state = get_state(server_one_test, token)

    assert py_state == state

    tick_server(server_one_test, ticks)
    game_server.tick(ticks)

    py_state = game_server.get_state(token)
    state = get_state(server_one_test, token)
    print(py_state)
    print(state)

    assert py_state == state


@pytest.mark.parametrize('map_id', ['map1', 'town'])
def test_move_sequence_one_player(server_one_test, game_server, map_id):
    name = 'name'

    params: dict = join_to_map(server_one_test, name, map_id).json()
    token = params['authToken']
    player_id = params['playerId']

    position, _, _ = get_parsed_state(server_one_test, token, player_id)
    game_server.join(name, map_id, token, player_id, Point(position[0], position[1]))

    valid_directions = ['R', 'L', 'U', 'D']

    random.seed(136)    # This particular seed brakes the actual server on 10th step (py-server works as expected)

    for i in range(0, 10):

        direction = valid_directions[random.randint(0, len(valid_directions) - 1)]
        ticks = random.randint(10, 10000)

        move_players(server_one_test, game_server, token, direction)
        tick_both(server_one_test, game_server, ticks)

        state = get_state(server_one_test, token)
        py_state = game_server.get_state(token)
        print(direction, ticks)
        print('Server:', state)
        print('PyServer:', py_state)

        assert state == py_state

