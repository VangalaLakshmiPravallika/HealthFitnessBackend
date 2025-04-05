def test_register(client):
    response = client.post('/api/register', 
                         json={"email": "test@example.com", "password": "test123"})
    assert response.status_code == 201
    assert "User registered successfully" in response.json["message"]

def test_login(client, auth):
    token = auth.login()
    assert isinstance(token, str)
    assert len(token) > 0

def test_protected_route(client, auth):
    token = auth.login()
    response = client.get('/api/get-profile',
                        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in [200, 404]  # 404 if no profile exists