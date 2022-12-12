import os
import json

import pytest
import requests

from xprocess import ProcessStarter
from urllib.parse import urljoin
from pathlib import Path
from contextlib import contextmanager
from typing import Set, Optional, Tuple

from cpp_server_api import CppServer as Server


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
