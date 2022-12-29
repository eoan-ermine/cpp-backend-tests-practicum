import os
import json

import pytest
import socket

from xprocess import ProcessStarter
from pathlib import Path
from contextlib import contextmanager
from typing import Set


from cpp_server_api import CppServer as Server
from cpp_server_api import PortIsAllocated
import docker.errors
import random

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

    yield Server(server_domain, server_port)

    xprocess.getinfo("server").terminate()


@pytest.fixture(scope='function')
def server_one_test(xprocess):
    with _make_server(xprocess) as result:
        yield result


@pytest.fixture(scope='function')
def docker_server():
    server_domain = os.environ.get('SERVER_DOMAIN', '127.0.0.1')
    image_name = os.environ['IMAGE_NAME']

    ports_list = find_open_ports(server_domain)

    while True:
        try:
            port_number = random.randint(0, len(ports_list))
            port = ports_list[port_number]
            ports_list.pop(port_number)
            server = Server(server_domain, port, image_name)
            return server

        except docker.errors.APIError:
            ports_list = find_open_ports(server_domain)

            pass
        except IndexError:
            ports_list = find_open_ports(server_domain)
        except KeyboardInterrupt:
            pass


def find_open_ports(domain):
    ports = []
    for port in range(8080, 8081):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((domain, port))
                ports.append(port)
            except OSError:
                continue
    return ports


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
