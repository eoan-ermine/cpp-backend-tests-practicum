import json

ans_list = """
[
  {
    "id": "map1",
    "name": "Map 1"
  }
]
"""
ans_list = json.dumps(ans_list, sort_keys=True)

ans_info = """
{
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
"""
ans_info = json.dumps(ans_info, sort_keys=True)


def test_list(myserver):
    request = 'api/v1/maps'
    res = myserver.get(f'/{name}')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == ans_list

def test_info(myserver):
    request = 'api/v1/maps/map1'
    res = myserver.get(f'/{name}')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/json'
    assert res.json() == ans_info
