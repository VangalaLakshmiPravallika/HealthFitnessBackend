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

@patch("app.achievements_collection.find")
def test_get_achievements(mock_find, client):
    mock_find.return_value = [{"title": "Well-Rested", "likes": 5}]
    res = client.get("/api/get-achievements", headers=auth_header())
    assert res.status_code == 200
    assert isinstance(res.json, list)

@patch("app.achievements_collection.update_one")
def test_like_achievement(mock_update, client):
    mock_update.return_value.modified_count = 1
    res = client.post("/api/like-achievement", headers=auth_header(), json={"title": "Well-Rested"})
    assert res.status_code == 200
    assert res.json["message"] == "Achievement liked!"

@patch("app.groups_collection.find_one")
@patch("app.groups_collection.insert_one")
def test_create_group(mock_insert, mock_find, client):
    mock_find.return_value = None
    res = client.post("/api/create-group", headers=auth_header(), json={"group_name": "TestGroup"})
    assert res.status_code == 201

@patch("app.groups_collection.find_one")
@patch("app.groups_collection.update_one")
def test_join_group(mock_update, mock_find, client):
    mock_find.return_value = {"name": "TestGroup", "members": []}
    res = client.post("/api/join-group", headers=auth_header(), json={"group_name": "TestGroup"})
    assert res.status_code == 200

@patch("app.groups_collection.find_one")
def test_get_group_details(mock_find, client):
    mock_find.return_value = {"name": "TestGroup", "members": ["test@example.com"]}
    res = client.get("/api/get-group-details/TestGroup", headers=auth_header())
    assert res.status_code == 200
    assert "name" in res.json

@patch("app.groups_collection.find_one")
@patch("app.groups_collection.delete_one")
def test_delete_group(mock_delete, mock_find, client):
    mock_find.return_value = {"name": "TestGroup", "members": ["test@example.com"]}
    res = client.post("/api/delete-group", headers=auth_header(), json={"group_name": "TestGroup"})
    assert res.status_code == 200

@patch("app.groups_collection.find_one")
@patch("app.groups_collection.update_one")
def test_leave_group(mock_update, mock_find, client):
    mock_find.return_value = {"name": "TestGroup", "members": ["test@example.com"]}
    res = client.post("/api/leave-group", headers=auth_header(), json={"group_name": "TestGroup"})
    assert res.status_code == 200

@patch("app.groups_collection.find_one")
@patch("app.groups_collection.update_one")
def test_group_post(mock_update, mock_find, client):
    mock_find.return_value = {"name": "TestGroup", "members": ["test@example.com"]}
    mock_update.return_value.modified_count = 1
    res = client.post("/api/group-post", headers=auth_header(), json={
        "group_name": "TestGroup",
        "content": "Hello Group!"
    })
    assert res.status_code == 201

@patch("app.notifications_collection.insert_one")
@patch("app.groups_collection.find_one")
@patch("app.groups_collection.update_one")
def test_like_post(mock_update, mock_find, mock_notify, client):
    mock_find.return_value = {
        "posts": [{"content": "Hello", "user": "someone@example.com"}]
    }
    mock_update.return_value.modified_count = 1
    res = client.post("/api/like-post", headers=auth_header(), json={
        "group_name": "TestGroup", "post_content": "Hello"
    })
    assert res.status_code == 200

@patch("app.notifications_collection.insert_one")
@patch("app.groups_collection.find_one")
@patch("app.groups_collection.update_one")
def test_comment_post(mock_update, mock_find, mock_notify, client):
    mock_find.return_value = {
        "posts": [{"content": "Hello", "user": "someone@example.com"}]
    }
    mock_update.return_value.modified_count = 1
    res = client.post("/api/comment-post", headers=auth_header(), json={
        "group_name": "TestGroup",
        "post_content": "Hello",
        "comment": "Nice one!"
    })
    assert res.status_code == 200

@patch("app.notifications_collection.find")
def test_get_notifications(mock_find, client):
    mock_find.return_value = [{"message": "Someone liked your post"}]
    res = client.get("/api/notifications", headers=auth_header())
    assert res.status_code == 200

@patch("app.groups_collection.find_one")
def test_get_group_posts(mock_find, client):
    mock_find.return_value = {
        "members": ["test@example.com"],
        "posts": [{"content": "Hi"}]
    }
    res = client.get("/api/get-group-posts/TestGroup", headers=auth_header())
    assert res.status_code == 200

@patch("app.groups_collection.find")
def test_get_groups(mock_find, client):
    mock_find.return_value = [{"name": "TestGroup"}]
    res = client.get("/api/get-groups")
    assert res.status_code == 200
    assert isinstance(res.json, list)

@patch("app.groups_collection.find")
def test_get_user_groups(mock_find, client):
    mock_find.return_value = [{"name": "TestGroup"}]
    res = client.get("/api/get-user-groups", headers=auth_header())
    assert res.status_code == 200
    assert "groups" in res.json

@patch("app.groups_collection.update_one")
def test_dislike_post(mock_update, client):
    mock_update.return_value.modified_count = 1
    res = client.post("/api/dislike-post", headers=auth_header(), json={
        "group_name": "TestGroup", "post_content": "Hello"
    })
    assert res.status_code == 200

@patch("app.groups_collection.update_one")
def test_remove_comment(mock_update, client):
    mock_update.return_value.modified_count = 1
    res = client.post("/api/remove-comment", headers=auth_header(), json={
        "group_name": "TestGroup",
        "post_content": "Hello",
        "comment": "Nice one!"
    })
    assert res.status_code == 200
