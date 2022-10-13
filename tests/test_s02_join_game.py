import pytest


def get_maps(server):
    request = 'api/v1/maps'
    res = server.get(request)
    return res.json()


def join_to_map(server, user_name, map_id):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    maps = get_maps(server)
    data = {"userName": user_name, "mapId": map_id}
    return server.request('POST', header, request, json=data)


def test_join_invalid_map(server):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": "Harry Potter", "mapId": '  invalid  '}
    res = server.request('POST', header, request, json=data)
    assert res.status_code == 404
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'mapNotFound'


def test_join_invalid_user_name(server):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    maps = get_maps(server)
    data = {"userName": "", "mapId": maps[0]['id']}
    res = server.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


def test_join_miss_user_name(server):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    maps = get_maps(server)
    data = {"mapId": maps[0]['id']}
    res = server.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


def test_join_miss_map_id(server):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": "Harry Potter"}
    res = server.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


def test_join_miss_data(server):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {}
    res = server.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


def test_join_invalid_data(server):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": "", "mapId": '   invalid   '}
    res = server.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()


@pytest.mark.parametrize('method', ['GET', 'OPTIONS', 'HEAD', 'PUT', 'PATCH', 'DELETE'])
def test_join_invalid_verb(server, method):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    res = server.request(method, header, request)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidMethod'


@pytest.mark.randomize(min_length=1, max_length=100, str_attrs=('printable',), ncalls=10)
def test_join_success(server, name: str, request):
    print(request.node)
    maps = get_maps(server)
    res = join_to_map(server, name, maps[0]['id'])
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert isinstance(res_json['playerId'], int)
    assert len(res_json['authToken']) == 32
    assert int(res_json['authToken'], 16)


def test_players_miss_token(server):
    request = 'api/v1/game/players'
    header = {'content-type': 'application/json'}
    res = server.request('GET', header, request)
    assert res.status_code == 401
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidToken'


def test_players_invalid_token(server):
    request = 'api/v1/game/players'
    header = {'content-type': 'application/json', 'authorization': 'Bearer'}
    res = server.request('GET', header, request)
    assert res.status_code == 401
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidToken'


def test_players_unknown_token(server):
    request = 'api/v1/game/players'
    header = {'content-type': 'application/json', 'authorization': 'Bearer 6516861d89ebfff147bf2eb2b5153ae1'}
    res = server.request('GET', header, request)
    assert res.status_code == 401
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'unknownToken'


@pytest.mark.parametrize('method', ['OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE'])
def test_players_invalid_verb(server, method):
    request = 'api/v1/game/players'
    header = {'content-type': 'application/json', 'authorization': 'Bearer 6516861d89ebfff147bf2eb2b5153ae1'}
    res = server.request(method, header, request)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidMethod'


def test_players_success(server):
    maps = get_maps(server)
    res = join_to_map(server, 'User1', maps[0]['id'])
    token1 = res.json()['authToken']
    res = join_to_map(server, 'User2', maps[0]['id'])
    token2 = res.json()['authToken']

    request = 'api/v1/game/players'
    header = {'content-type': 'application/json', 'authorization': f'Bearer {token1}'}
    res = server.request('GET', header, request)
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json1 = res.json()

    header = {'content-type': 'application/json', 'authorization': f'Bearer {token2}'}
    res = server.request('GET', header, request)
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json2 = res.json()

    assert res_json1 == res_json2
