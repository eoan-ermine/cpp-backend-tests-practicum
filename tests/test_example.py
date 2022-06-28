

def test_ping(myserver):
    res = myserver.get('/ping')
    assert res.status_code == 200
    assert res.text == 'pong'


def test_pong(myserver):
    res = myserver.get('/pong')
    assert res.status_code == 200
    assert res.text == 'ping'


def test_hello(myserver):
    name = 'John'
    res = myserver.get(f'/hello/{name}')
    assert res.status_code == 200
    assert res.text == f'Hello {name}!'


def test_goodbye(myserver):
    name = 'John'
    res = myserver.get(f'/goodbye/{name}')
    assert res.status_code == 200
    assert res.text == f'Goodbye {name}!'
