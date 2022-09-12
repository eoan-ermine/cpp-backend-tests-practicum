import json

ans_list = [
  {
    "id": "map1",
    "name": "Map 1"
  }
]

ans_info = {
  "id": "map1",
  "name": "Map 1",
  "roads": [
    {
      "x0": 0,
      "y0": 0,
      "x1": 40
    },
    {
      "x0": 40,
      "y0": 0,
      "y1": 30
    },
    {
      "x0": 40,
      "y0": 30,
      "x1": 0
    },
    {
      "x0": 0,
      "y0": 0,
      "y1": 30
    }
  ],
  "buildings": [
    {
      "x": 5,
      "y": 5,
      "w": 30,
      "h": 20
    }
  ],
  "offices": [
    {
      "id": "o0",
      "x": 40,
      "y": 30,
      "offsetX": 5,
      "offsetY": 0
    }
  ]
}

map_not_found = {
  "code": "mapNotFound",
  "message": "Map not found"
}

bad_request = {
  "code": "badRequest",
  "message": "Bad request"
}

def test_list(myserver):
    request = 'api/v1/maps'
    res = myserver.get(f'/{request}')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == ans_list

def test_info(myserver):
    request = 'api/v1/maps/map1'
    res = myserver.get(f'/{request}')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == ans_info

def test_map_not_found(myserver):
    request = 'api/v1/maps/map33'
    res = myserver.get(f'/{request}')
    assert res.status_code == 404
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == map_not_found

def test_bad_request(myserver):
    request = 'api/v333/maps/map1'
    res = myserver.get(f'/{request}')
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == bad_request

def test_image(myserver):
    request = '/images/cube.svg'
    res = myserver.get(f'/{request}')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'image/svg+xml'

def test_file_not_found(myserver):
    request = '/images/ccccube.svg'
    res = myserver.get(f'/{request}')
    assert res.status_code == 404
    assert res.headers['content-type'] == 'text/plain'

def test_file_bad_request(myserver):
    request = '/files/no_file'
    res = myserver.get(f'/{request}')
    assert res.status_code == 400
    assert res.headers['content-type'] == 'text/plain'
