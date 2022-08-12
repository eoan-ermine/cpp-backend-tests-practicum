def test_hello(myserver):
    name = 'Baron'
    res = myserver.get(f'/{name}')
    assert res.status_code == 200
    assert res.text == f'Hello, {name}'
    assert res.headers['content-type'] == 'text/html'
    assert res.headers['content-length'] == 12

def test_hello_error(myserver):
    name = 'Baron'
    res = myserver.post(f'/{name}', f'some')
    assert res.status_code == 405
    assert res.text == f'Invalid method'
    assert res.headers['content-type'] == 'text/html'
    assert res.headers['content-length'] == 14
