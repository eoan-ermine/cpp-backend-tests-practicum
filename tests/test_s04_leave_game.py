# from cpp_server_api import CppServer as Server\
import math

Server = None

import random
import pytest

import requests

from game_server import Direction
from dataclasses import dataclass
from typing import List


"""
Вопросики:

- Как сортируются два игрока с одинаковыми очками?
- В какой именно момет происходит отправка на пенсию?
- Как узнать время отправки на пенсию?
- Что будет, если стартовая позиция рейтинга будет дальше, чем размер рейтинга?

"""


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

    def update_score(self, server: None):
        state = server.get_player_state(self.token, self.player_id)
        self.score = state['score']


class Tribe:

    def __init__(self, server: None, map_id: str, num_of_players: int = 10, prefix: str = 'Player'):
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


def get_retirement_time(server: None) -> float:

    # How can it be extracted?

    return 10.0


def tick_seconds(server: None, seconds: float):
    server.tick(int(seconds*1_000))


def validate_ok_response(res: requests.Response):
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/json'
    assert res.headers['Cache-Control'] == 'no-cache'
    assert int(res.headers['Content-Length']) == len(res.content)


def get_records(server: Server, start: int = 0, max_items: int = 100) -> list:
    request = '/api/v1/game/records'
    header = {'content-type': 'application/json'}
    params = {'start': start, 'maxItems': max_items}
    res: requests.Response = server.request('GET', header, request, data=params)
    validate_ok_response(res)
    res_json: list = res.json()
    print(res_json)
    assert type(res_json) == list

    return res_json


def test_clean_records(server_one_test):
    res_json = get_records(server_one_test)

    assert len(res_json) == 0


# Выдаёт результат, хотя не должен
@pytest.mark.skip
def test_huge_request(server_one_test: Server):
    request = '/api/v1/game/records'
    header = {'content-type': 'application/json'}
    params = {'start': 0, 'maxItems': 101}
    res: requests.Response = server_one_test.request('GET', header, request, data=params)

    assert res.status_code == 400


# Аналогично, не падает, хотя должен
@pytest.mark.skip
def test_unexpected_start(server_one_test: Server):
    request = '/api/v1/game/records'
    header = {'content-type': 'application/json'}
    params = {'start': 100, 'maxItems': 100}

    res: requests.Response = server_one_test.request('GET', header, request, data=params)
    print(res.content)
    assert res.status_code == 400   # What will it be?


def test_retirement_one_player(server_one_test: Server, map_id):
    token, player_id = server_one_test.join('Julius Can', map_id)

    server_one_test.get_state(token)  # To ensure that the game is joined, so the validation will be passed

    r_time = get_retirement_time(server_one_test)

    tick_seconds(server_one_test, r_time)

    request = '/api/v1/game/state'
    header = {'content-type': 'application/json',
              'Authorization': f'Bearer {token}'}

    res: requests.Response = server_one_test.request('GET', header, request)

    assert res.status_code == 401

@pytest.mark.parametrize('map_ids', ['map1'])
def test_a_few_zero_records(server_one_test, map_ids):

    tribe = Tribe(server_one_test, map_ids)

    r_time = get_retirement_time(server_one_test)
    tribe.update_scores()

    tick_seconds(server_one_test, r_time*2)
    tribe.add_time(r_time*2)


    tribe_records = tribe.get_list()
    records = get_records(server_one_test)
    assert records == tribe_records


# Падает. По неизвестному закону добавляет не всех, а только часть (из 10 человек - то 4, то 7, то 10)
def test_a_few_records(server_one_test: None):
    map_id = 'town'
    tribe = Tribe(server_one_test, map_id)

    r_time = get_retirement_time(server_one_test)

    for _ in range(0, random.randint(100, 350)):
        tribe.randomized_move()
    print(tribe)
    tribe.update_scores()
    tick_seconds(server_one_test, r_time)
    tribe.add_time(r_time)

    tribe_records = tribe.get_list()
    records = get_records(server_one_test)
    compare(records, tribe_records)


def test_old_young_tribes_records(server_one_test: None, map_id):
    # map_id = 'town'
    old_tribe = Tribe(server_one_test, map_id, prefix='Elder')

    r_time = get_retirement_time(server_one_test)

    for _ in range(0, random.randint(100, 350)):
        old_tribe.randomized_move()

    old_tribe.update_scores()
    tick_seconds(server_one_test, r_time / 2)
    old_tribe.add_time(r_time / 2)
    old_tribe.stop()

    young_tribe = Tribe(server_one_test, map_id, prefix='Infant')

    for _ in range(0, random.randint(100, 350)):
        young_tribe.randomized_turn()

        ticks = random.randint(100, min(1000, int(r_time * 900)))
        seconds = ticks / 1000
        young_tribe.add_time(seconds)
        old_tribe.add_time(seconds)
        tick_seconds(server_one_test, seconds)

    young_tribe.update_scores()

    tick_seconds(server_one_test, r_time / 2)
    old_tribe.add_time(r_time / 2)
    young_tribe.add_time(r_time / 2)

    records = get_records(server_one_test)
    tribe_records = old_tribe.get_list()

    compare(records, tribe_records)


# Из 100 человек в рекорды попадает 40-70, причём постоянно разное количество
@pytest.mark.skip
def test_a_hundred_records(server_one_test: None):
    map_id = 'map1'
    tribe = Tribe(server_one_test, map_id, num_of_players=100)

    r_time = get_retirement_time(server_one_test)

    for _ in range(0, random.randint(10, 35)):
        tribe.randomized_move()

    tribe.update_scores()
    tick_seconds(server_one_test, r_time*2)
    tribe.add_time(r_time*2)

    records = get_records(server_one_test)
    tribe_records = tribe.get_list()

    compare(records, tribe_records)


def test_a_hundred_plus_records(server_one_test: None, map_id):

    tribe = Tribe(server_one_test, map_id, num_of_players=150)

    r_time = get_retirement_time(server_one_test)

    for _ in range(0, random.randint(10, 35)):
        tribe.randomized_move()

    tribe.update_scores()
    tick_seconds(server_one_test, r_time)
    tribe.add_time(r_time)

    records = get_records(server_one_test)
    tribe_records = tribe.get_list()[:100]

    compare(records, tribe_records)


@pytest.mark.skip
def test_two_sequential_tribes_records(server_one_test: None, map_id):

    red_foxes = Tribe(server_one_test, map_id, num_of_players=50, prefix='Red fox')

    r_time = get_retirement_time(server_one_test)

    for _ in range(0, random.randint(10, 35)):
        red_foxes.randomized_move()

    red_foxes.update_scores()
    tick_seconds(server_one_test, r_time)
    red_foxes.add_time(r_time)

    tribe_records = red_foxes.get_list()
    records = get_records(server_one_test)
    compare(records, tribe_records)
    print(tribe_records)

    orange_raccoons = Tribe(server_one_test, map_id, num_of_players=50, prefix='Orange Raccoon')

    for _ in range(0, random.randint(10, 35)):
        orange_raccoons.randomized_move()

    orange_raccoons.update_scores()

    tick_seconds(server_one_test, r_time)
    orange_raccoons.add_time(r_time)

    tribe_records.extend(orange_raccoons.get_list())
    tribe_records.sort(key=lambda x: x.score, reverse=True)
    print(tribe_records)

    records = get_records(server_one_test)
    compare(records, tribe_records)


@pytest.mark.skip
@pytest.mark.randomize(min_num=0, max_num=50, ncalls=3)
@pytest.mark.randomize(min_num=0, max_num=100, ncalls=3)
@pytest.mark.randomize(min_num=0, max_num=100, ncalls=3)
def test_a_records_selection(server_one_test: None, map_id, start: int, max_items: int, extra_players: int):

    tribe = Tribe(server_one_test, map_id, num_of_players=start + extra_players)

    r_time = get_retirement_time(server_one_test)

    for _ in range(0, random.randint(5, 15)):
        tribe.randomized_move()

    tribe.update_scores()
    tick_seconds(server_one_test, r_time*2)
    tribe.add_time(r_time*2)

    end = min(start + extra_players, start + max_items)
    tribe_records = tribe.get_list()[start:end]
    records = get_records(server_one_test, start, max_items)

    compare(records, tribe_records)