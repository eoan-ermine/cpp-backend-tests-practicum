import os
import pytest
import requests

from xprocess import ProcessStarter
from dataclasses import dataclass
from urllib.parse import urljoin
from pathlib import Path


@dataclass
class Server:
    url: str

    def get(self, endpoint):
        return requests.get(urljoin(self.url, endpoint))

    def post(self, endpoint, data):
        return requests.post(urljoin(self.url, endpoint), data)


@pytest.fixture(scope='module')
def myserver(xprocess):
    path = os.environ['DELIVERY_APP']
    if not Path(path).exists():
        raise Exception(f"no such file {os.environ['DELIVERY_APP']}")

    class Starter(ProcessStarter):
        pattern = 'Running on'
        args = [path]

    xprocess.ensure("myserver", Starter)

    yield Server('http://127.0.0.1:8080/')

    xprocess.getinfo("myserver").terminate()
