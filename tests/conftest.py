import os
import json

import pytest
import requests

from xprocess import ProcessStarter
from urllib.parse import urljoin
from pathlib import Path
from contextlib import contextmanager
from typing import Set, Optional, Tuple


class WrongHeaders(ValueError, KeyError):
    """Header doesn't have proper content-type, cache-control, or/and content-length"""


class WrongCode(ValueError):
    """The responses status code is wrong"""


class BadlyEncodedJson(json.decoder.JSONDecodeError):
    """The content isn't encoded right"""


class BadResponse(ValueError):
    """The content of the response doesn't match the expected structure or values"""


class Server:

    def __init__(self, url: str, output: Optional[Path] = None):
        self.url = url
        if output:
            self.file = open(output)

    def get_line(self):
        return self.file.readline()

    def get_log(self):
        return json.loads(self.get_line())

    def request(self, method, header, url, **kwargs):
        req = requests.Request(method, urljoin(self.url, url), headers=header, **kwargs).prepare()
        with requests.Session() as session:
            return session.send(req)

    def get(self, endpoint):
        return requests.get(urljoin(self.url, endpoint))

    def post(self, endpoint, data):
        return requests.post(urljoin(self.url, endpoint), data)

    def get_maps(self) -> Optional[dict]:
        request = 'api/v1/maps'
        res: requests.Response = self.get(request)
        self.validate_response(res)
        res_json = res.json()
        return res_json

    def get_map(self, map_id: str) -> Optional[dict]:
        request = 'api/v1/maps/' + map_id
        res: requests.Response = self.get(request)
        self.validate_response(res)
        return res.json()

    def join(self, player_name: str, map_id: str) -> Optional[dict]:
        request = 'api/v1/game/join'
        header = {'content-type': 'application/json'}
        data = {"userName": player_name, "mapId": map_id}
        res = self.request('POST', header, request, json=data)
        self.validate_response(res)
        return res.json()

    def add_player(self, player_name: str, map_id: str) -> Tuple[str, str]:
        params = self.join(player_name, map_id)
        try:
            token = params['authToken']
            player_id = params['playerId']
        except KeyError as ke:
            raise BadResponse(f'Error while getting the added player parameters: "{ke.args[0]}" is missing. '
                              f'Response: {params}')
        return token, player_id

    def get_state(self, token) -> Optional[dict]:
        request = '/api/v1/game/state'
        header = {'content-type': 'application/json',
                  'Authorization': f'Bearer {token}'}

        res = self.request('GET', header, request)
        self.validate_response(res)
        return res.json()

    def get_player_state(self, token, player_id):
        game_session_state = self.get_state(token)
        players = game_session_state.get('players')

        try:
            state = players[str(player_id)]
        except KeyError:
            raise BadResponse(f'The given game session state doesn\'t '
                              f'have the desired player id "{player_id}": {players}')
        except AttributeError:
            raise BadResponse(f'The given game session state doesn\'t '
                              f'appear to have "players" field: {game_session_state}')

        return state

    def move(self, token: str, direction: str):
        request = '/api/v1/game/player/action'
        header = {'content-type': 'application/json', 'Authorization': f'Bearer {token}'}
        data = {"move": direction}
        res = self.request('POST', header, request, json=data)
        self.validate_response(res)

    def tick(self, ticks: int):
        request = 'api/v1/game/tick'
        header = {'content-type': 'application/json'}
        data = {"timeDelta": ticks}
        res = self.request('POST', header, request, json=data)
        self.validate_response(res)

    @staticmethod
    def validate_response(res: requests.Response):
        if res.status_code != 200:
            raise WrongCode(f'Status code isn\'t OK: 200 != {res.status_code}')
        try:
            if res.headers['content-type'] != 'application/json':
                raise WrongHeaders(f'Wrong Content-Type header: '   # Should it be split into four different exceptions?
                                   f'"{res.headers["content-type"]}" instead of "application/json"')
            if res.headers['cache-control'] != 'no-cache':
                raise WrongHeaders(f'Wrong Cache-Control header: '
                                   f'"{res.headers["cache-control"]}" instead of "no-cache"')
            if res.request.method != 'HEAD':
                if int(res.headers['content-length']) != len(res.content):
                    raise WrongHeaders(f'Wrong content length: '
                                       f'"{res.headers["content-length"]}" instead of "{len(res.content)}"')
            else:
                if res.headers['content-length'] != 0:
                    raise WrongHeaders(f'Wrong content length: '
                                       f'"{res.headers["content-length"]}" instead of "0" for HEAD request')
        except KeyError as ke:
            raise WrongHeaders(f'Wrong response headers: missing "{ke.args[0]}". Headers: {res.headers}')

        try:
            res.json()
        except json.decoder.JSONDecodeError as je:
            raise BadlyEncodedJson(msg=je.msg, doc=je.doc, pos=je.pos)


def get_maps_from_config_file(config: Path):
    return json.loads(config.read_text())['maps']


def pytest_generate_tests(metafunc):
    config_path = os.environ.get('CONFIG_PATH')
    if 'map_dict' in metafunc.fixturenames:
        if config_path:
            config_path = Path(config_path)
            metafunc.parametrize(
                'map_dict',
                [
                    pytest.param(map_dict, id=map_dict['name'])
                    for map_dict in get_maps_from_config_file(config_path)
                ],
            )
    if 'config' in metafunc.fixturenames:
        if config_path:
            config_path = Path(config_path)
            metafunc.parametrize(
                'config',
                json.loads(config_path.read_text())
            )
    if 'map_id' in metafunc.fixturenames:
        if config_path:
            config_path = Path(config_path)
            metafunc.parametrize(
                'map_id',
                [
                    pytest.param(map_dict['id'], id=map_dict['id'])
                    for map_dict in json.loads(config_path.read_text())['maps']
                ],
            )


@pytest.fixture(scope='module')
def server(xprocess):
    with _make_server(xprocess) as result:
        yield result


@contextmanager
def _make_server(xprocess):
    commands = os.environ['COMMAND_RUN'].split()
    server_domain = os.environ.get('SERVER_DOMAIN', '127.0.0.1')
    server_port = os.environ.get('SERVER_PORT', '8080')

    class Starter(ProcessStarter):
        pattern = '[Ss]erver (has )?started'
        args = commands

    _, output_path = xprocess.ensure("server", Starter)

    yield Server(f'http://{server_domain}:{server_port}/', output_path)

    xprocess.getinfo("server").terminate()


@pytest.fixture(scope='function')
def server_one_test(xprocess):
    with _make_server(xprocess) as result:
        yield result


def get_maps(server):
    request = 'api/v1/maps'
    res = server.get(request)
    return res.json()


def join_to_map(server, user_name: str, map_id: str):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": user_name, "mapId": map_id}
    return server.request('POST', header, request, json=data)


def sort_by_id(lst: list):
    return sorted(lst, key=lambda x: x['id'])


def get_maps_from_config(config: dict):
    return sort_by_id([
        {'id': map_dict['id'], 'name': map_dict['name']}
        for map_dict
        in config['maps']
    ])


def tick(server, delta: int):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}
    data = {"timeDelta": delta}
    res = server.request('POST', header, request, json=data)
    assert res.status_code == 200
    return res


def check_allow(header_allow: str, allows: Set[str]):
    expected = set(verb.strip() for verb in header_allow.split(','))
    assert expected == allows


class Road:
    def __init__(self, coordinates: dict):
        x0 = coordinates['x0']
        y0 = coordinates['y0']
        x1 = coordinates.get('x1', x0)
        y1 = coordinates.get('y1', y0)
        self.x0 = min(x0, x1)
        self.x1 = max(x0, x1)
        self.y0 = min(y0, y1)
        self.y1 = max(y0, y1)

    def contains(self, x, y):
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1
