from unittest.mock import patch  
def test_register(client):
    response = client.post('/api/register', json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    assert "registered" in response.json['message']

def test_login(client):
    client.post('/api/register', json={"email": "login@example.com", "password": "pass"})
    response = client.post('/api/login', json={"email": "login@example.com", "password": "pass"})
    assert response.status_code == 200
    assert "token" in response.json

def test_forgot_password(client, app):
    app.users_collection.insert_one({"email": "user@example.com"})
    with patch('app.mail.send'):  
        response = client.post('/api/forgot-password', json={"email": "user@example.com"})
        assert response.status_code == 200