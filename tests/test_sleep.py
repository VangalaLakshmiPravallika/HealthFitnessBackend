import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

from flask_jwt_extended import create_access_token

def auth_header(email="test@example.com"):
    with app.app_context():
        token = create_access_token(identity=email)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

@patch("app.sleep_collection.find")
def test_get_sleep_streak(mock_find, client):
    today = datetime.utcnow().date()
    mock_find.return_value.sort.return_value = [
        {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d")}
        for i in range(3)  
    ]

    res = client.get("/api/sleep-streak", headers=auth_header())
    assert res.status_code == 200
    assert res.json["streak"] == 3

@patch("app.user_challenges_collection.update_one")
def test_reset_sleep(mock_update, client):
    mock_update.return_value = None
    res = client.post("/api/reset-sleep", headers=auth_header())
    assert res.status_code == 200
    assert res.json["message"] == "Sleep value reset successfully!"

@patch("app.achievements_collection.insert_one")
@patch("app.sleep_collection.insert_one")
def test_log_sleep(mock_insert, mock_achievements, client):
    data = {
        "sleep_hours": 7.5,
        "sleep_rating": 4,
        "date": datetime.utcnow().strftime("%Y-%m-%d")
    }

    res = client.post("/api/log-sleep", headers=auth_header(), json=data)
    assert res.status_code == 201
    assert "message" in res.json
    assert res.json["achievement"] == "🌙 Well-Rested Badge"

@patch("app.sleep_collection.find")
def test_get_sleep_history(mock_find, client):
    mock_data = [
        {"date": "2025-04-06", "sleep_hours": 7.5},
        {"date": "2025-04-05", "sleep_hours": 6.0},
        {"date": "2025-04-04", "sleep_hours": 5.5}
    ]
    mock_find.return_value.sort.return_value.limit.return_value = mock_data

    res = client.get("/api/sleep-history", headers=auth_header())
    assert res.status_code == 200
    assert "history" in res.json
    assert "sleep_quality" in res.json
    assert "sleep_distribution" in res.json
