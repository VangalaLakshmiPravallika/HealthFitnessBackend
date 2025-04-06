import pytest
from flask_jwt_extended import create_access_token
from flask import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, profiles_collection 

@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def auth_header():
    with app.app_context():
        email = "testuser@example.com"
        token = create_access_token(identity=email)
        return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_profile(monkeypatch):
    sample_profile = {
        "email": "testuser@example.com",
        "bmi": 22.5,
        "preferred_body_part": "chest",
        "equipment": ["barbell", "body weight"],
        "workout_history": [
            {"exerciseId": 1},
            {"exerciseId": 2},
            {"exerciseId": 1},
            {"exerciseId": 3},
        ],
    }

    def mock_find_one(query):
        return sample_profile if query.get("email") == "testuser@example.com" else None

    monkeypatch.setattr(profiles_collection, "find_one", mock_find_one)

# -- Tests --

def test_get_recommendations_success(client, auth_header):
    """Test general recommendations endpoint"""
    response = client.get("/api/get-recommendations", headers=auth_header)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert "recommended_workouts" in json_data
    assert isinstance(json_data["recommended_workouts"], list)
    assert len(json_data["recommended_workouts"]) > 0
    assert "gifUrl" in json_data["recommended_workouts"][0]

def test_get_personalized_workouts_success(client, auth_header, mock_profile):
    """Test personalized workout endpoint with profile + history"""
    response = client.get("/api/get-personalized-workouts", headers=auth_header)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert "recommended_workouts" in json_data
    assert "intensity_level" in json_data
    assert "bmi" in json_data
    assert isinstance(json_data["recommended_workouts"], list)
    assert len(json_data["recommended_workouts"]) > 0
    assert "gifUrl" in json_data["recommended_workouts"][0]

def test_get_personalized_workouts_missing_bmi(client, auth_header, monkeypatch):
    """Test personalized endpoint with missing BMI"""
    def mock_find_one(query):
        return {
            "email": "testuser@example.com"
        }

    monkeypatch.setattr(profiles_collection, "find_one", mock_find_one)
    response = client.get("/api/get-personalized-workouts", headers=auth_header)
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["success"] is False
    assert "BMI not found" in json_data["error"]

def test_get_personalized_workouts_no_profile(client, auth_header, monkeypatch):
    """Test personalized endpoint with no user profile found"""
    def mock_find_one(query):
        return None

    monkeypatch.setattr(profiles_collection, "find_one", mock_find_one)
    response = client.get("/api/get-personalized-workouts", headers=auth_header)
    assert response.status_code == 400 or response.status_code == 500
    json_data = response.get_json()
    assert json_data["success"] is False
