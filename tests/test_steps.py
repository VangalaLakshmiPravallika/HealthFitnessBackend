import pytest
from datetime import datetime, timedelta
from flask import Flask
from flask_jwt_extended import create_access_token
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, steps_collection, sleep_collection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test_secret_key'
    with app.test_client() as client:
        yield client

def auth_header(email="testuser@example.com"):
    with app.app_context():
        token = create_access_token(identity=email)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

@patch.object(steps_collection, 'find_one')
@patch.object(steps_collection, 'insert_one')
@patch.object(steps_collection, 'update_one')
def test_update_steps(mock_update, mock_insert, mock_find, client):
    mock_find.return_value = None  

    response = client.post(
        "/api/update-steps",
        json={"steps": 5000},
        headers=auth_header()
    )

    assert response.status_code == 200
    assert response.json["message"] == "Steps updated successfully!"

@patch("app.get_current_date")
@patch.object(steps_collection, 'find_one')
def test_get_steps(mock_find, mock_date, client):
    mock_date.return_value = "2025-04-06"
    mock_find.return_value = {"steps": 8000}

    response = client.get("/api/get-steps", headers=auth_header())
    assert response.status_code == 200
    assert response.json["steps"] == 8000

@patch.object(steps_collection, 'find_one')
@patch.object(steps_collection, 'aggregate')
def test_get_step_history(mock_aggregate, mock_find, client):
    mock_find.return_value = {"steps": 6000}
    mock_aggregate.side_effect = [
        iter([{"total": 15000}]),  
        iter([{"total": 55000}])   
    ]

    response = client.get("/api/get-step-history", headers=auth_header())
    assert response.status_code == 200
    assert response.json["daily"] == 6000
    assert response.json["weekly"] == 15000
    assert response.json["monthly"] == 55000

@patch.object(sleep_collection, 'find')
def test_sleep_streak(mock_find, client):
    today = datetime.utcnow().date()
    streak_dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    mock_find.return_value.sort.return_value = [{"date": d} for d in streak_dates]

    response = client.get("/api/sleep-streak", headers=auth_header())
    assert response.status_code == 200
    assert response.json["streak"] == 5

def test_update_steps_invalid(client):
    response = client.post("/api/update-steps", json={}, headers=auth_header())
    assert response.status_code == 400
    assert "error" in response.json

