import os
import pytest
import requests
import time

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
        pattern = ''
        args = [path]

    time.sleep(15)

    xprocess.ensure("myserver", Starter)

    time.sleep(15)

    yield Server('http://127.0.0.1:8080/')

    time.sleep(15)

    xprocess.getinfo("myserver").terminate()
