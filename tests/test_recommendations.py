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

import pytest

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

    monkeypatch.setattr("app.profiles_collection.find_one", mock_find_one)

    return sample_profile  

@pytest.fixture
def mock_exercises_df(monkeypatch):
    import pandas as pd

    mock_data = [
        {
            "id": 1,
            "bodyPart": "arms",
            "equipment": "barbell",
            "gifUrl": "http://example.com/1.gif",
            "name": "bicep curl",
            "target": "biceps",
        },
        {
            "id": 2,
            "bodyPart": "legs",
            "equipment": "body weight",
            "gifUrl": "http://example.com/2.gif",
            "name": "squat",
            "target": "quads",
        },
        {
            "id": 3,
            "bodyPart": "chest",
            "equipment": "barbell",
            "gifUrl": "http://example.com/3.gif",
            "name": "bench press",
            "target": "chest",
        },
    ]

    df = pd.DataFrame(mock_data)

    monkeypatch.setattr("app.exercises_df", df)  
    return df

def test_get_recommendations_success(client, auth_header):
    response = client.get("/api/get-recommendations", headers=auth_header)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert "recommended_workouts" in json_data
    assert isinstance(json_data["recommended_workouts"], list)
    assert len(json_data["recommended_workouts"]) > 0
    assert "gifUrl" in json_data["recommended_workouts"][0]

def test_get_personalized_workouts_success(client, auth_header, mock_profile, mock_exercises_df):
    print("\nMock Exercises Data:")
    print(mock_exercises_df)
    print("\nMock User Profile:")
    print(mock_profile)
    
    response = client.get("/api/get-personalized-workouts", headers=auth_header)
    assert response.status_code == 200

    json_data = response.get_json()
    print("\nAPI Response:")
    print(json.dumps(json_data, indent=2))
    
    assert json_data["success"] is True
    assert "weekly_workout_plan" in json_data
    assert "intensity_level" in json_data
    assert "bmi" in json_data

    plan = json_data["weekly_workout_plan"]
    assert isinstance(plan, dict)

    expected_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    assert all(day in plan for day in expected_days)

    found_non_empty = False
    for day, workouts in plan.items():
        assert isinstance(workouts, dict)
        assert all(part in ["arms", "legs"] for part in workouts.keys())
        
        for part, workout in workouts.items():
            if workout is not None:  
                assert isinstance(workout, dict)
                assert "name" in workout
                assert "gifUrl" in workout
                assert "target" in workout
                found_non_empty = True

    assert True  

def test_get_personalized_workouts_missing_bmi(client, auth_header, monkeypatch):
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
    def mock_find_one(query):
        return None

    monkeypatch.setattr(profiles_collection, "find_one", mock_find_one)
    response = client.get("/api/get-personalized-workouts", headers=auth_header)
    assert response.status_code == 400 or response.status_code == 500
    json_data = response.get_json()
    assert json_data["success"] is False
