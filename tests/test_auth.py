from unittest.mock import patch
import pytest

def test_register(client):
    """Test user registration endpoint"""
    test_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    # Test successful registration
    response = client.post('/api/register', json=test_data)
    assert response.status_code == 201
    assert response.json['message'] == "User registered successfully"
    assert "id" in response.json
    
    # Test duplicate registration
    duplicate_response = client.post('/api/register', json=test_data)
    assert duplicate_response.status_code == 409
    assert "already exists" in duplicate_response.json['error']

def test_login(client):
    """Test user login endpoint"""
    # Setup test user
    register_data = {
        "email": "login@example.com", 
        "password": "validPassword123!"
    }
    client.post('/api/register', json=register_data)
    
    # Test successful login
    response = client.post('/api/login', json=register_data)
    assert response.status_code == 200
    assert "access_token" in response.json
    assert "refresh_token" in response.json
    
    # Test invalid credentials
    invalid_response = client.post('/api/login', json={
        "email": "login@example.com",
        "password": "wrongpassword"
    })
    assert invalid_response.status_code == 401
    assert "Invalid credentials" in invalid_response.json['error']

def test_forgot_password(client, app):
    """Test password reset functionality"""
    test_email = "user@example.com"
    
    # Setup test user
    app.users_collection.insert_one({
        "email": test_email,
        "password": "existing_password"
    })
    
    # Mock email sending
    with patch('app.mail.send') as mock_send:
        response = client.post(
            '/api/forgot-password',
            json={"email": test_email}
        )
        
        # Verify response
        assert response.status_code == 200
        assert "reset link sent" in response.json['message'].lower()
        
        # Verify email was attempted to be sent
        mock_send.assert_called_once()
        
    # Test non-existent email
    invalid_response = client.post(
        '/api/forgot-password',
        json={"email": "nonexistent@example.com"}
    )
    assert invalid_response.status_code == 404