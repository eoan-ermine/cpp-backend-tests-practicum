from cpp_server_api import CppServer
import math
import random
import pytest
import os

import requests

from game_server import Direction
from dataclasses import dataclass
from typing import List


def validate_ok_response(res: requests.Response):
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/json'
    assert res.headers['Cache-Control'] == 'no-cache'
    assert int(res.headers['Content-Length']) == len(res.content)


def get_records(server, start: int = 0, max_items: int = 100) -> list:
    request = '/api/v1/game/records'
    header = {'content-type': 'application/json'}
    params = {'start': start, 'maxItems': max_items}
    res: requests.Response = server.request('GET', header, request, data=params)
    validate_ok_response(res)
    res_json: list = res.json()
    assert type(res_json) == list

    return res_json


def test_clean_records(server_one_test):
    res_json = get_records(server_one_test)

    assert len(res_json) == 0
