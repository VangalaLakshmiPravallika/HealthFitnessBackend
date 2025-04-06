import pytest
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app 

def auth_header(email="test@example.com"):
    with flask_app.app_context():
        token = create_access_token(identity=email)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

@pytest.fixture
def user_email():
    return "test@example.com"

@pytest.fixture
def valid_profile_data():
    return {
        "name": "John Doe",
        "age": 30,
        "gender": "male",
        "height": 1.75,
        "weight": 70,
        "goals": "maintain"
    }

@patch("app.profiles_collection.update_one")
@patch("app.get_jwt_identity")
def test_store_profile_success(mock_identity, mock_update, client, valid_profile_data, user_email):
    mock_identity.return_value = user_email
    mock_update.return_value = MagicMock()

    res = client.post("/api/store-profile", json=valid_profile_data, headers=auth_header())
    data = res.get_json()

    assert res.status_code == 201
    assert "bmi" in data
    assert "daily_calories" in data
    assert data["message"] == "Profile stored successfully"

@patch("app.get_jwt_identity")
def test_store_profile_missing_fields(mock_identity, client):
    mock_identity.return_value = "test@example.com"
    res = client.post("/api/store-profile", json={"name": "Alice"}, headers=auth_header())

    assert res.status_code == 400
    assert res.get_json()["error"] == "Missing required fields"

@patch("app.get_jwt_identity")
def test_store_profile_invalid_data(mock_identity, client):
    mock_identity.return_value = "test@example.com"
    data = {
        "name": "Invalid",
        "age": "abc",
        "gender": "male",
        "height": 1.75,
        "weight": 70
    }
    res = client.post("/api/store-profile", json=data, headers=auth_header())
    assert res.status_code == 400
    assert "Invalid data format" in res.get_json()["error"]

@patch("app.profiles_collection.update_one")
@patch("app.get_jwt_identity")
def test_edit_profile_success(mock_identity, mock_update, client):
    mock_identity.return_value = "test@example.com"
    mock_update.return_value = MagicMock()

    res = client.put("/api/edit-profile", json={
        "name": "John",
        "age": 28,
        "height": 1.7,
        "weight": 68
    }, headers=auth_header())

    assert res.status_code == 200
    assert res.get_json()["message"] == "Profile updated successfully"

@patch("app.get_jwt_identity")
def test_edit_profile_no_fields(mock_identity, client):
    mock_identity.return_value = "test@example.com"

    res = client.put("/api/edit-profile", json={}, headers=auth_header())
    assert res.status_code == 400
    assert res.get_json()["error"] == "No fields to update"

@patch("app.profiles_collection.find_one")
@patch("app.get_jwt_identity")
def test_get_profile_success(mock_identity, mock_find, client):
    mock_identity.return_value = "test@example.com"
    mock_find.return_value = {
        "email": "test@example.com",
        "name": "Alice",
        "age": 25,
        "gender": "female",
        "height": 1.65,
        "weight": 60,
        "bmi": 22.04,
        "daily_calories": 1188.0,
        "goals": "gain"
    }

    res = client.get("/api/get-profile", headers=auth_header())
    data = res.get_json()

    assert res.status_code == 200
    assert data["name"] == "Alice"
    assert data["bmi"] == 22.04

@patch("app.profiles_collection.find_one")
@patch("app.get_jwt_identity")
def test_get_profile_not_found(mock_identity, mock_find, client):
    mock_identity.return_value = "test@example.com"
    mock_find.return_value = None

    res = client.get("/api/get-profile", headers=auth_header())
    assert res.status_code == 404
    assert res.get_json()["error"] == "Profile not found"
