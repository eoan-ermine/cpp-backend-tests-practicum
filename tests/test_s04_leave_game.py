from cpp_server_api import CppServer
import math
import random
import pytest
import os

import requests

from game_server import Direction
from dataclasses import dataclass
from typing import List


import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_connection(db_name):
    return psycopg2.connect(user=os.environ.get('POSTGRES_USER', 'postgres'),
                            password=os.environ.get('POSTGRES_PASSWORD', 'Mys3Cr3t'),
                            host=os.environ.get('POSTGRES_HOST', '172.17.0.2'),
                            port=os.environ.get('POSTGRES_PORT', '5432'),
                            dbname=db_name
                            )


@pytest.fixture(autouse=True)
def recreate_db():
    conn = get_connection(None)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF NOT EXISTS records --force')
    except Exception:
        raise

    with conn.cursor() as cur:
        cur.execute(f'create database records')

    conn.close()


if __name__ == '__main__':
    conn = get_connection(None)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        cur.execute(f'create database records')


def compare(records: List[dict], tribe_records: List[dict]):
    assert len(records) == len(tribe_records)
    for record in records:
        name = record['name']
        for t_record in tribe_records:
            if t_record['name'] == name:

                # math.isclose(record['playTime'], t_record['playTime'], rel_tol=)
                math.isclose(record['score'], t_record['score'])


@dataclass
class Player:

    name: str
    token: str
    player_id: int
    score: float = 0
    playing_time: float = 0.0

    def add_time(self, time_to_add: float):
        self.playing_time += time_to_add

    def get_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "playTime": self.playing_time
        }

    def update_score(self, server):
        state = server.get_player_state(self.token, self.player_id)
        self.score = state['score']


class Tribe:

    def __init__(self, server, map_id: str, num_of_players: int = 10, prefix: str = 'Player'):
        self.server: None = server
        self.players: List[Player] = list()
        for i in range(0, num_of_players):
            name = f'{prefix} {i}'
            token, player_id = server.join(name, map_id)
            self.players.append(Player(name, token, player_id))

    def __getitem__(self, index: int) -> Player:
        return self.players[index]

    def add_time(self, time_to_add: float):
        for pl in self.players:
            pl.add_time(time_to_add)

    # def

    def get_list(self) -> list:
        self.players.sort(key=lambda x: x.score, reverse=True)
        res = [pl.get_dict() for pl in self.players]

        return res

    def update_scores(self):
        for player in self.players:
            player.update_score(self.server)

    def randomized_turn(self):
        for pl in self.players:
            direction = Direction.random_str()
            self.server.move(pl.token, direction)

    def randomized_move(self):
        r_time = get_retirement_time(self.server)
        self.randomized_turn()
        ticks = random.randint(100, min(10000, int(r_time*900)))
        seconds = ticks / 1000
        self.add_time(seconds)
        tick_seconds(self.server, seconds)

    def stop(self):
        for pl in self.players:
            self.server.move(pl.token, '')


def get_retirement_time(server) -> float:

    # How can it be extracted?

    return 10.0


def tick_seconds(server, seconds: float):
    server.tick(int(seconds*1_000))


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


def test_retirement_one_standing_player(server_one_test, map_id):
    token, player_id = server_one_test.join('Julius Can', map_id)
    r_time = get_retirement_time(server_one_test)

    server_one_test.get_state(token)  # To ensure that the game is joined, so the validation will be passed

    tick_seconds(server_one_test, r_time - 0.001)

    server_one_test.get_state(token)  # To ensure that the game is joined, so the validation will be passed
    tick_seconds(server_one_test, 0.001)

    request = '/api/v1/game/state'
    header = {'content-type': 'application/json',
              'Authorization': f'Bearer {token}'}

    res: requests.Response = server_one_test.request('GET', header, request)

    assert res.status_code == 401

    records = get_records(server_one_test)
    assert records[0] == {'name': 'Julius Can', 'score': 0, 'playTime': r_time}


def test_retirement_one_player(server_one_test, map_id):
    token, player_id = server_one_test.join('Julius Can', map_id)
    r_time = get_retirement_time(server_one_test)

    server_one_test.get_state(token)  # To ensure that the game is joined, so the validation will be passed

    random.seed(1011)

    for _ in range(100):
        direction = Direction.random_str()
        server_one_test.move(token, direction)
        server_one_test.tick(random.randint(10, int(r_time * 900)))

    state = server_one_test.get_player_state(token, player_id)
    score = state['score']

    tick_seconds(server_one_test, r_time)

    request = '/api/v1/game/state'
    header = {'content-type': 'application/json',
              'Authorization': f'Bearer {token}'}

    res: requests.Response = server_one_test.request('GET', header, request)

    # assert res.status_code == 401
    records = get_records(server_one_test)
    assert records[0]['name'] == 'Julius Can'
    assert math.isclose(float(records[0]['score']), score)


def test_a_few_zero_records(server_one_test, map_id):

    tribe = Tribe(server_one_test, map_id)

    r_time = get_retirement_time(server_one_test)
    tribe.update_scores()

    tick_seconds(server_one_test, r_time)
    tribe.add_time(r_time)

    tribe_records = tribe.get_list()
    records = get_records(server_one_test)
    compare(records, tribe_records)
