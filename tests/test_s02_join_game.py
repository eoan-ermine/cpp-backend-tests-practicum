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


def test_join_success(myserver_in_docker):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    maps = get_maps(myserver_in_docker)
    data = {"userName": "Harry Potter", "mapId": maps[0]['id']}
    res = myserver_in_docker.request('POST', header, request, json=data)
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


def test_join_invalid_data(myserver_in_docker):
    request = 'api/v1/game/join'
    header = {'content-type': 'application/json'}
    data = {"userName": "", "mapId": '   invalid   '}
    res = myserver_in_docker.request('GET', header, request, json=data)
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.headers['cache-control'] == 'no-cache'
    res_json = res.json()
