import json

map_not_found = {
  "code": "mapNotFound",
  "message": "Map not found"
}

bad_request = {
  "code": "badRequest",
  "message": "Bad request"
}


def get_maps(myserver_in_docker):
    request = 'api/v1/maps'
    res = myserver_in_docker.get(request)
    return res.json()


def join_to_map(myserver_in_docker, user_name, map_id):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    maps = get_maps(myserver_in_docker)
    data = {"userName": user_name, "mapId": map_id}
    return myserver_in_docker.request('POST', header, request, json=data)


def test_join_success(myserver_in_docker):
    maps = get_maps(myserver_in_docker)
    res = join_to_map(myserver_in_docker, 'Harry Potter', maps[0]['id'])
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    assert res_json['playerId'] == 0
    assert len(res_json['authToken']) == 32
    assert int(res_json['authToken'], 16)


def test_join_invalid_map(myserver_in_docker):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": "Harry Potter", "mapId": '  invalid  '}
    res = myserver_in_docker.request('POST', header, request, json=data)
    assert res.status_code == 404
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'mapNotFound'


def test_join_invalid_user_name(myserver_in_docker):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    maps = get_maps(myserver_in_docker)
    data = {"userName": "", "mapId": maps[0]['id']}
    res = myserver_in_docker.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


def test_join_miss_user_name(myserver_in_docker):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    maps = get_maps(myserver_in_docker)
    data = {"mapId": maps[0]['id']}
    res = myserver_in_docker.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


def test_join_miss_map_id(myserver_in_docker):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": "Harry Potter"}
    res = myserver_in_docker.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


def test_join_miss_data(myserver_in_docker):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {}
    res = myserver_in_docker.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidArgument'


def test_join_invalid_data(myserver_in_docker):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": "", "mapId": '   invalid   '}
    res = myserver_in_docker.request('POST', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()


def test_join_invalid_verb(myserver_in_docker):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": "", "mapId": '   invalid   '}
    res = myserver_in_docker.request('GET', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidMethod'


def test_players_success(myserver_in_docker):
    maps = get_maps(myserver_in_docker)
    res = join_to_map(myserver_in_docker, 'User1', maps[0]['id'])
    token1 = res.json()['authToken']
    res = join_to_map(myserver_in_docker, 'User2', maps[0]['id'])
    token2 = res.json()['authToken']

    request = 'api/v1/game/players'
    header = {'content-type': 'application/json', 'authorization': f'Bearer {token1}'}
    res = myserver_in_docker.request('GET', header, request)
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json1 = res.json()

    header = {'content-type': 'application/json', 'authorization': f'Bearer {token2}'}
    res = myserver_in_docker.request('GET', header, request)
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json2 = res.json()

    assert res_json1 == res_json2


def test_players_miss_token(myserver_in_docker):
    request = 'api/v1/game/players'
    header = {'content-type': 'application/json'}
    res = myserver_in_docker.request('GET', header, request)
    assert res.status_code == 401
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidToken'


def test_players_invalid_token(myserver_in_docker):
    request = 'api/v1/game/players'
    header = {'content-type': 'application/json', 'authorization': 'Bearer'}
    res = myserver_in_docker.request('GET', header, request)
    assert res.status_code == 401
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidToken'


def test_players_unknown_token(myserver_in_docker):
    request = 'api/v1/game/players'
    header = {'content-type': 'application/json', 'authorization': 'Bearer 6516861d89ebfff147bf2eb2b5153ae1'}
    res = myserver_in_docker.request('GET', header, request)
    assert res.status_code == 401
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'unknownToken'


def test_players_invalid_verb(myserver_in_docker):
    request = 'api/v1/game/players'
    header = {'content-type': 'application/json', 'authorization': 'Bearer 6516861d89ebfff147bf2eb2b5153ae1'}
    res = myserver_in_docker.request('POST', header, request)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
    print(res_json)
    assert res_json['code'] == 'invalidMethod'
