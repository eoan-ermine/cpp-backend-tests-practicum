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

def test_list(myserver_in_docker):
    request = 'api/v1/maps'
    res = myserver_in_docker.get(f'/{request}')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == ans_list

def test_info(myserver_in_docker):
    request = 'api/v1/maps/map1'
    res = myserver_in_docker.get(f'/{request}')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == ans_info

def test_map_not_found(myserver_in_docker):
    request = 'api/v1/maps/map33'
    res = myserver_in_docker.get(f'/{request}')
    assert res.status_code == 404
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == map_not_found

def test_bad_request(myserver_in_docker):
    request = 'api/v333/maps/map1'
    res = myserver_in_docker.get(f'/{request}')
    assert res.status_code == 400
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == bad_request

def test_image(myserver_in_docker):
    request = 'images/cube.svg'
    res = myserver_in_docker.get(f'/{request}')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'image/svg+xml'

def test_file_not_found(myserver_in_docker):
    request = 'images/ccccube.svg'
    res = myserver_in_docker.get(f'/{request}')
    assert res.status_code == 404
    assert res.headers['content-type'] == 'text/html'

def test_index_html(myserver_in_docker):
    request = 'index.html'
    res = myserver_in_docker.get(f'/{request}')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'text/html'
    request2 = ''
    res2 = myserver_in_docker.get(f'/{request2}')
    assert res2.status_code == 200
    assert res2.headers['content-type'] == 'text/html'
    assert res2.text == res.text

def test_logs(myserver_in_docker):
    log_json = myserver_in_docker.get_log()
    assert log_json['message'] == 'Server has started...'
    assert log_json['data']['port'] == 8080
    assert log_json['data']['address'] == '0.0.0.0'
    request = 'images/cube.svg'
    res = myserver_in_docker.get(f'/{request}')
    log_json = myserver_in_docker.get_log()
    assert log_json['message'] == 'request received'
    assert log_json['data']['ip'] == '127.0.0.1'
    assert log_json['data']['URI'] == '/images/cube.svg'
    assert log_json['data']['method'] == 'GET'
    print(log_json)
    assert 1 == 2
