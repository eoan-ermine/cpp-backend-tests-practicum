def test_hello(myserver):
    name = 'Baron'
    res = myserver.get(f'/{name}')
    assert res.status_code == 200
    assert res.text == f'Hello, {name}!'
