import pytest
import requests


def get_maps(server):
    request = 'api/v1/maps'
    res = server.get(request)
    return res.json()


def join_to_map(server, user_name, map_id):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": user_name, "mapId": map_id}
    return server.request('POST', header, request, json=data)


def test_tick_miss_delta(server):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}

    res = server.request('POST', header, request)

    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


@pytest.mark.parametrize('delta', {0.0, '0', True})
def test_tick_invalid_type_delta(server, delta):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}

    data = {"timeDelta": delta}
    res = server.request('POST', header, request, json=data)

    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


@pytest.mark.parametrize('method', {'GET', 'OPTIONS', 'HEAD', 'PUT', 'PATCH', 'DELETE'})
def test_tick_invalid_verb(server, method):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}
    res = server.request(method, header, request)
    print(res.headers)
    assert res.status_code == 405
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'

    if method != 'HEAD':
        res_json = res.json()
        assert res_json['code'] == 'invalidMethod'


@pytest.mark.randomize(min_num=0, max_num=10000, ncalls=10)
def test_tick_success(server, delta: int):
    request = 'api/v1/game/tick'
    header = {'content-type': 'application/json'}
    data = {"timeDelta": delta}
    res = server.request('POST', header, request, json=data)

    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'

    res_json = res.json()
    print(res_json)
    assert res_json == dict()


