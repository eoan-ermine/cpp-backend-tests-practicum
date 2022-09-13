import os
import pytest
import requests

from xprocess import ProcessStarter
from dataclasses import dataclass
from urllib.parse import urljoin
from pathlib import Path
from typing import Optional


@dataclass
class Server:
    url: str

    def get(self, endpoint):
        return requests.get(urljoin(self.url, endpoint))

    def post(self, endpoint, data):
        return requests.post(urljoin(self.url, endpoint), data)


def is_env_path(env_name: str) -> Optional[str]:
    path = os.environ.get(env_name)
    if path and not Path(path).exists():
        raise FileNotFoundError(f"no such file {path}")
    return path


@pytest.fixture(scope='module')
def myserver(xprocess):
    path = is_env_path('DELIVERY_APP')
    config_path = is_env_path('CONFIG_PATH')
    data_path = is_env_path('DATA_PATH')

    args_ = list()
    if path:
        args_.append(path)
    if config_path:
        args_.append(config_path)
    if data_path:
        args_.append(data_path)

    class Starter(ProcessStarter):
        pattern = 'Server has started...'
        args = args_

    xprocess.ensure("myserver", Starter)
    yield Server('http://127.0.0.1:8080/')

    xprocess.getinfo("myserver").terminate()
