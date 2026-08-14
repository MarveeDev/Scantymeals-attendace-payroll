def test_login_success(client):
    response = client.post('/login', data={'username': 'testadmin', 'password': 'testpass'})
    assert response.status_code == 302 # Redirect to dashboard
    
def test_login_fail(client):
    response = client.post('/login', data={'username': 'testadmin', 'password': 'wrong'})
    assert b'Invalid username or password' in response.data
    
def test_protected_route(client):
    response = client.get('/')
    assert response.status_code == 302 # Redirect to login
    
def test_logout(auth_client):
    response = auth_client.get('/logout')
    assert response.status_code == 302
    
    # Access protected route again
    res2 = auth_client.get('/')
    assert res2.status_code == 302
