import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, users_collection, profiles_collection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    test_client = app.test_client()

    users_collection.delete_many({"email": "testuser@example.com"})
    profiles_collection.delete_many({"email": "testuser@example.com"})

    yield test_client

    users_collection.delete_many({"email": "testuser@example.com"})
    profiles_collection.delete_many({"email": "testuser@example.com"})


def test_register_success(client):
    response = client.post("/api/register", json={
        "email": "testuser@example.com",
        "password": "testpass123"
    })

    assert response.status_code == 201
    assert response.get_json()["message"] == "User registered successfully"


def test_register_duplicate(client):
    client.post("/api/register", json={
        "email": "testuser@example.com",
        "password": "testpass123"
    })
    response = client.post("/api/register", json={
        "email": "testuser@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_login_success(client):
    client.post("/api/register", json={
        "email": "testuser@example.com",
        "password": "testpass123"
    })

    profiles_collection.insert_one({
        "email": "testuser@example.com",
        "name": "Test",
        "age": 25,
        "gender": "Other",
        "height": 170,
        "weight": 70
    })

    response = client.post("/api/login", json={
        "email": "testuser@example.com",
        "password": "testpass123"
    })

    data = response.get_json()
    assert response.status_code == 200
    assert "token" in data
    assert data["profileComplete"] is True


def test_login_wrong_password(client):
    client.post("/api/register", json={
        "email": "testuser@example.com",
        "password": "testpass123"
    })

    response = client.post("/api/login", json={
        "email": "testuser@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401
    assert "error" in response.get_json()


def test_login_missing_fields(client):
    response = client.post("/api/login", json={"email": ""})
    assert response.status_code == 400
    assert "error" in response.get_json()
