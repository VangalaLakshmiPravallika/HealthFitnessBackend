import pytest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app
from flask_jwt_extended import create_access_token

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def auth_header(email="test@example.com"):
    with app.app_context():
        token = create_access_token(identity=email)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

@patch("app.challenges_collection.find")
def test_get_challenges(mock_find, client):
    mock_find.return_value = [
        {"name": "Water Challenge", "target": 30, "unit": "days"}
    ]
    res = client.get("/api/get-challenges", headers=auth_header())
    assert res.status_code == 200
    assert isinstance(res.json["challenges"], list)
    assert res.json["challenges"][0]["name"] == "Water Challenge"

@patch("app.challenges_collection.find_one")
@patch("app.user_challenges_collection.find_one")
@patch("app.user_challenges_collection.insert_one")
def test_join_challenge(mock_insert, mock_user_find, mock_chal_find, client):
    mock_chal_find.return_value = {
        "name": "Water Challenge",
        "target": 30,
        "unit": "days"
    }
    mock_user_find.return_value = None  

    res = client.post(
        "/api/join-challenge",
        json={"challenge_name": "Water Challenge"},
        headers=auth_header()
    )
    assert res.status_code == 201
    assert res.json["message"] == "Joined challenge: Water Challenge"


@patch("app.challenges_collection.find_one")
@patch("app.user_challenges_collection.find_one")
def test_join_challenge_already_joined(mock_user_find, mock_chal_find, client):
    mock_chal_find.return_value = {
        "name": "Water Challenge",
        "target": 30,
        "unit": "days"
    }
    mock_user_find.return_value = {
        "email": "test@example.com",
        "challenge_name": "Water Challenge"
    }

    res = client.post(
        "/api/join-challenge",
        json={"challenge_name": "Water Challenge"},
        headers=auth_header()
    )

    assert res.status_code == 400
    assert res.json["message"] == "You have already joined this challenge"


@patch("app.user_challenges_collection.find")
def test_get_user_challenges(mock_find, client):
    mock_find.return_value = [
        {"challenge_name": "Water Challenge", "progress": 10}
    ]

    res = client.get("/api/get-user-challenges", headers=auth_header())

    assert res.status_code == 200
    assert isinstance(res.json["challenges"], list)
    assert res.json["challenges"][0]["challenge_name"] == "Water Challenge"
    assert res.json["challenges"][0]["progress"] == 10

@patch("app.get_jwt_identity")
@patch("app.user_challenges_collection.find_one")
@patch("app.user_challenges_collection.update_one")
@patch("app.challenges_collection.find_one") 
def test_update_challenge_progress(mock_challenge_find, mock_update, mock_user_find, mock_identity, client):

    mock_identity.return_value = "test@example.com"
    mock_challenge_find.return_value = {
        "name": "Water Challenge",
        "target": 30
    }
    mock_user_find.return_value = {
        "email": "test@example.com",
        "challenge_name": "Water Challenge",
        "progress": 10,
        "target": 30
    }
    mock_update.return_value.modified_count = 1

    res = client.post(
        "/api/update-challenge-progress",
        json={"challenge_name": "Water Challenge", "progress": 5},
        headers=auth_header()
    )

    print("Response JSON:", res.json)
    assert res.status_code == 200

@patch("app.user_challenges_collection.find_one")
@patch("app.user_challenges_collection.delete_one")
def test_leave_challenge(mock_delete, mock_find, client):
    mock_find.return_value = {"challenge_name": "Water Challenge"}
    mock_delete.return_value.deleted_count = 1  

    res = client.post(
        "/api/leave-challenge",
        json={"challenge_name": "Water Challenge"},
        headers=auth_header()
    )

    print("Response JSON:", res.json)
    assert res.status_code == 200

