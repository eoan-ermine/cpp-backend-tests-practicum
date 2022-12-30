import logging
import time

import docker.errors

from cpp_server_api import CppServer
import math
import random
import pytest
import os
import logging

import requests

from game_server import Direction
from dataclasses import dataclass
from typing import List
from cpp_server_api import CppServer as Server

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2.errors

from xprocess import ProcessStarter
from contextlib import contextmanager

import socket


def get_connection(db_name):
    return psycopg2.connect(user=os.environ.get('POSTGRES_USER', 'postgres'),
                            password=os.environ.get('POSTGRES_PASSWORD', 'Mys3Cr3t'),
                            host=os.environ.get('POSTGRES_HOST', '172.17.0.2'),
                            port=os.environ.get('POSTGRES_PORT', '5432'),
                            dbname=db_name
                            )


def flush_db(db_name):
    conn = get_connection(None)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS {db_name} --force')
        cur.execute(f'create database {db_name}')
    conn.close()


def find_open_ports():
    server_domain = os.environ.get('SERVER_DOMAIN', '127.0.0.1')
    ports = []
    for port in range(8080, 8081):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((server_domain, port))
                ports.append(port)
            except OSError:
                continue
    return ports


global_ports_list = find_open_ports()


@pytest.fixture(scope='function')
def postgres_server():

    server_domain = os.environ.get('SERVER_DOMAIN', '127.0.0.1')
    image_name = os.environ.get('IMAGE_NAME')
    user = os.environ.get('POSTGRES_USER', 'postgres')
    password = os.environ.get('POSTGRES_PASSWORD', 'Mys3Cr3t')
    host = os.environ.get('POSTGRES_HOST', '172.17.0.2')
    postgres_port = os.environ.get('POSTGRES_PORT', '5432')

    is_running = False
    # global ports_list
    ports_list = [port for port in range(49001, 49150)]
    while not is_running:
        if len(ports_list) < 0:
            ports_list = find_open_ports()
        try:
            port_number = random.randint(0, len(ports_list))
            port = ports_list[port_number]
            ports_list.pop(port_number)
            db_name = f'db_for_port{port}'
            flush_db(db_name)
            args = {
                'environment': {
                    'GAME_DB_URL': f'postgres://{user}:{password}@{host}:{postgres_port}/{db_name}'
                    }
            }
            server = Server(server_domain, port, image_name, **args)
            return server
            # ports_list.append(port)
            # print('Ports: ', ports_list)
            # server.container.stop()

        except docker.errors.APIError:
            # print('Port was busy')
            ports_list = find_open_ports()

            pass
        except psycopg2.errors.UniqueViolation:
            # print('Database was already exist')
            ports_list = find_open_ports()

            pass
        except psycopg2.errors.ObjectInUse:
            # print('Database was accessed by someone else then trying to drop')
            ports_list = find_open_ports()

            pass
        except IndexError:
            # print('Run out of ports')
            ports_list = find_open_ports()
        except KeyboardInterrupt:
            pass
            # print(ports_list)


def compare(records: List[dict], tribe_records: List[dict]):
    assert len(records) == len(tribe_records)
    for record in records:
        name = record['name']
        for t_record in tribe_records:
            if t_record['name'] == name:
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
    return 15.0


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


def test_clean_records(postgres_server):
    res_json = get_records(postgres_server)
    assert len(res_json) == 0


def test_retirement_one_standing_player(postgres_server, map_id):
    token, player_id = postgres_server.join('Julius Can', map_id)
    r_time = get_retirement_time(postgres_server)
    postgres_server.get_state(token)  # To ensure that the game is joined, so the validation will be passed
    tick_seconds(postgres_server, r_time - 0.001)
    postgres_server.get_state(token)  # To ensure that the game is joined, so the validation will be passed
    tick_seconds(postgres_server, 0.001)

    request = '/api/v1/game/state'
    header = {'content-type': 'application/json',
              'Authorization': f'Bearer {token}'}

    res: requests.Response = postgres_server.request('GET', header, request)

    assert res.status_code == 401

    records = get_records(postgres_server)
    assert records[0] == {'name': 'Julius Can', 'score': 0, 'playTime': r_time}


def test_retirement_one_player(postgres_server, map_id):
    token, player_id = postgres_server.join('Julius Can', map_id)
    r_time = get_retirement_time(postgres_server)
    postgres_server.get_state(token)  # To ensure that the game is joined, so the validation will be passed

    for _ in range(100):
        direction = Direction.random_str()
        postgres_server.move(token, direction)
        postgres_server.tick(random.randint(10, int(r_time * 900)))

    state = postgres_server.get_player_state(token, player_id)
    score = state['score']
    postgres_server.move(token, '')
    tick_seconds(postgres_server, r_time)

    request = '/api/v1/game/state'
    header = {'content-type': 'application/json',
              'Authorization': f'Bearer {token}'}

    res: requests.Response = postgres_server.request('GET', header, request)
    assert res.status_code == 401

    records = get_records(postgres_server)
    assert records[0]['name'] == 'Julius Can'
    assert math.isclose(float(records[0]['score']), score)


def test_a_few_zero_records(postgres_server, map_id):
    tribe = Tribe(postgres_server, map_id)
    r_time = get_retirement_time(postgres_server)
    tribe.update_scores()
    tick_seconds(postgres_server, r_time)
    tribe.add_time(r_time)
    tribe_records = tribe.get_list()
    records = get_records(postgres_server)
    compare(records, tribe_records)


def test_a_few_records(postgres_server, map_id):
    tribe = Tribe(postgres_server, map_id)
    r_time = get_retirement_time(postgres_server)

    for _ in range(0, random.randint(100, 350)):
        tribe.randomized_move()

    tribe.update_scores()
    tribe.stop()
    tick_seconds(postgres_server, r_time)
    tribe.add_time(r_time)

    tribe_records = tribe.get_list()
    records = get_records(postgres_server)
    compare(records, tribe_records)


def test_old_young_tribes_records(postgres_server, map_id):
    old_tribe = Tribe(postgres_server, map_id, prefix='Elder')
    r_time = get_retirement_time(postgres_server)

    for _ in range(0, random.randint(50, 200)):
        old_tribe.randomized_move()

    old_tribe.update_scores()
    tick_seconds(postgres_server, r_time / 2)
    old_tribe.add_time(r_time / 2)
    old_tribe.stop()

    young_tribe = Tribe(postgres_server, map_id, prefix='Infant')

    for _ in range(0, random.randint(50, 200)):
        young_tribe.randomized_turn()

        ticks = random.randint(100, min(1000, int(r_time * 900)))
        seconds = ticks / 1000
        young_tribe.add_time(seconds)
        old_tribe.add_time(seconds)
        tick_seconds(postgres_server, seconds)

    young_tribe.update_scores()
    tick_seconds(postgres_server, r_time / 2)
    old_tribe.add_time(r_time / 2)
    young_tribe.add_time(r_time / 2)

    records = get_records(postgres_server)
    tribe_records = old_tribe.get_list()

    compare(records, tribe_records)



def test_a_hundred_records(postgres_server, map_id):
    tribe = Tribe(postgres_server, map_id, num_of_players=100)
    r_time = get_retirement_time(postgres_server)

    for _ in range(0, random.randint(10, 35)):
        tribe.randomized_move()

    tribe.update_scores()
    tribe.stop()
    tick_seconds(postgres_server, r_time)
    tribe.add_time(r_time)

    records = get_records(postgres_server)
    tribe_records = tribe.get_list()

    compare(records, tribe_records)



def test_a_hundred_plus_records(postgres_server, map_id):
    tribe = Tribe(postgres_server, map_id, num_of_players=150)
    r_time = get_retirement_time(postgres_server)
    for _ in range(0, random.randint(10, 35)):
        tribe.randomized_move()
    tribe.update_scores()
    tribe.stop()
    tick_seconds(postgres_server, r_time)
    tribe.add_time(r_time)

    records = get_records(postgres_server)
    tribe_records = tribe.get_list()[:100]

    compare(records, tribe_records)


def test_two_sequential_tribes_records(postgres_server, map_id):
    red_foxes = Tribe(postgres_server, map_id, num_of_players=50, prefix='Red fox')
    r_time = get_retirement_time(postgres_server)

    for _ in range(0, random.randint(10, 35)):
        red_foxes.randomized_move()

    red_foxes.update_scores()
    red_foxes.stop()

    tick_seconds(postgres_server, r_time)
    red_foxes.add_time(r_time)
    tribe_records = red_foxes.get_list()
    records = get_records(postgres_server)
    compare(records, tribe_records)

    orange_raccoons = Tribe(postgres_server, map_id, num_of_players=50, prefix='Orange Raccoon')

    for _ in range(0, random.randint(10, 35)):
        orange_raccoons.randomized_move()

    orange_raccoons.update_scores()
    orange_raccoons.stop()

    tick_seconds(postgres_server, r_time)
    orange_raccoons.add_time(r_time)

    tribe_records.extend(orange_raccoons.get_list())
    tribe_records.sort(key=lambda x: x['score'], reverse=True)

    records = get_records(postgres_server)
    compare(records, tribe_records)


def test_reload_server(postgres_server, map_id):
    tribe = Tribe(postgres_server, map_id, num_of_players=50)
    r_time = get_retirement_time(postgres_server)
    for _ in range(0, random.randint(10, 35)):
        tribe.randomized_move()
    tribe.update_scores()
    tribe.stop()
    tick_seconds(postgres_server, r_time)
    tribe.add_time(r_time)

    records = get_records(postgres_server)
    tribe_records = tribe.get_list()[:100]

    compare(records, tribe_records)

    postgres_server.container.reload()
    reloaded_records = get_records(postgres_server)

    compare(records, reloaded_records)


@pytest.mark.skip
# @pytest.mark.randomize(min_num=0, max_num=50, ncalls=3)
# @pytest.mark.randomize(min_num=0, max_num=100, ncalls=3)
# @pytest.mark.randomize(min_num=0, max_num=100, ncalls=3)
@pytest.mark.parametrize('start', [0])
@pytest.mark.parametrize('max_items', [1])
@pytest.mark.parametrize('extra_players', [2])
def test_a_records_selection(postgres_server, map_id, start, max_items, extra_players):
    tribe = Tribe(postgres_server, map_id, num_of_players=start + extra_players)

    r_time = get_retirement_time(postgres_server)

    for _ in range(0, random.randint(5, 15)):
        tribe.randomized_move()

    tribe.update_scores()
    tribe.stop()

    tick_seconds(postgres_server, r_time)
    tribe.add_time(r_time)

    end = min(start + extra_players, start + max_items)
    tribe_records = tribe.get_list()[start:end]
    records = get_records(postgres_server, start, max_items)
    print(records)
    print(tribe_records)


    # compare(records, tribe_records)

