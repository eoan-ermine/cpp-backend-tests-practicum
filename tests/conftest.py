import os
import json

import pytest
import requests

from xprocess import ProcessStarter
from urllib.parse import urljoin
from pathlib import Path
from typing import Optional


class Server:

    def __init__(self, url, path):
        self.url = url
        self.file = open(path)
        # self.file.readline()

    def get_line(self):
        return self.file.readline()

    def get_log(self):
        return json.loads(self.get_line())

    def request(self, method, header, url, **kwargs):
        req = requests.Request(method, self.url+url, headers=header, **kwargs).prepare()
        with requests.Session() as session:
            return session.send(req)

    def get(self, endpoint):
        return requests.get(urljoin(self.url, endpoint))

    def post(self, endpoint, data):
        return requests.post(urljoin(self.url, endpoint), data)


def is_env_path(env_name: str) -> Optional[str]:
    path = os.environ.get(env_name)
    if path and not Path(path).exists():
        raise FileNotFoundError(f"no such file or directory {path}")
    return path


@pytest.fixture(scope='module')
def myserver(xprocess):
    path = is_env_path('DELIVERY_APP')
    config_path = is_env_path('CONFIG_PATH')
    data_path = is_env_path('DATA_PATH')

    if not path:
        raise Exception('DELIVERY_APP')
    args_ = [path]

    if config_path:
        args_.append(config_path)
    if data_path:
        args_.append(data_path)

    class Starter(ProcessStarter):
        pattern = 'Server has started...'
        args = args_

    _, path = xprocess.ensure("myserver", Starter)
    yield Server('http://127.0.0.1:8080/', path)

    xprocess.getinfo("myserver").terminate()


@pytest.fixture(scope='module')
def myserver_in_docker(xprocess):
    commands = os.environ['COMMAND_RUN'].split()
    server_domain = os.environ['SERVER_DOMAIN']

    class Starter(ProcessStarter):
        pattern = 'Server has started...'
        args = commands

    _, path = xprocess.ensure("myserver_in_docker", Starter)

    yield Server(f'http://{server_domain}:8080/', path)

    xprocess.getinfo("myserver_in_docker").terminate()
