import pytest
from flask import Flask, json
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import mongomock
import random
from unittest.mock import patch, MagicMock

# Add parent directory to Python path to import app.py
sys.path.append(str(Path(__file__).parent.parent))

# Now import your Flask app
from app import app as flask_app

load_dotenv()

# Mock MongoDB setup
@pytest.fixture
def mock_db():
    client = mongomock.MongoClient()
    db = client.HealthFitnessApp
    return db

@pytest.fixture
def app(mock_db):
    # Configure test settings
    flask_app.config['TESTING'] = True
    flask_app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    # Mock database collections
    flask_app.db = mock_db
    flask_app.users_collection = mock_db.users
    flask_app.profiles_collection = mock_db.profiles
    flask_app.sleep_collection = mock_db.sleep
    flask_app.achievements_collection = mock_db.achievements
    flask_app.groups_collection = mock_db.groups
    flask_app.meal_collection = mock_db.meals
    flask_app.badges_collection = mock_db.badges
    flask_app.progress_collection = mock_db.progress
    flask_app.steps_collection = mock_db.steps
    flask_app.challenges_collection = mock_db.challenges
    flask_app.user_challenges_collection = mock_db.user_challenges
    flask_app.notifications_collection = mock_db.notifications
    
    # Establish application context
    with flask_app.app_context():
        yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """Fixture to get authenticated headers"""
    # Clear any existing test data
    from app import users_collection
    users_collection.delete_many({"email": "test@example.com"})
    
    # Register a test user
    test_user = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    register_response = client.post('/api/register', json=test_user)
    print(f"Register response: {register_response.status_code}, {register_response.json}")
    assert register_response.status_code == 201

    # Login to get token
    login_response = client.post('/api/login', json=test_user)
    print(f"Login response: {login_response.status_code}, {login_response.json}")
    assert login_response.status_code == 200
    assert "token" in login_response.json, "Token not found in login response"
    
    token = login_response.json['token']
    return {'Authorization': f'Bearer {token}'}

def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json == {"message": "Flask API is running!"}

def test_register(client, mock_db):
    # Verify mock_db is empty
    assert mock_db.users.count_documents({}) == 0
    
    # Test data that passes all validations
    test_data = {
        "email": "valid@example.com", 
        "password": "longenoughpassword"
    }

    # Debug: Print collections before test
    print("Collections before test:", mock_db.list_collection_names())
    
    with patch('app.bcrypt.generate_password_hash', return_value='mockedhash'):
        response = client.post('/api/register', json=test_data)
    
    # Debug output
    print("Response:", response.status_code, response.json)
    print("Users in DB:", list(mock_db.users.find({})))
    
    # Verify response
    assert response.status_code == 201
    assert response.json['message'] == "User registered successfully!"
    
    # Verify database
    user = mock_db.users.find_one({"email": "valid@example.com"})
    assert user is not None, f"User not found. DB contents: {list(mock_db.users.find({}))}"
    assert user['password'] == 'mockedhash'

def test_login(client, mock_db):
    """Comprehensive login endpoint testing with mock collections"""
    # Debug setup
    print("\n=== Starting test_login ===")
    
    # Setup test data
    test_email = "pravalliva11@gmail.com"
    test_password = "prava30"

    # Clear test data
    mock_db.users.delete_many({})
    print("Cleared test users")

    # Register test user
    print(f"Registering user: {test_email}")
    register_response = client.post('/api/register', json={
        "email": test_email,
        "password": test_password
    })
    print(f"Register response: {register_response.status_code}, {register_response.json}")
    assert register_response.status_code == 201

    # Verify user was created
    db_user = mock_db.users.find_one({"email": test_email})
    print(f"User in DB: {db_user}")
    assert db_user is not None
    print(f"Stored password hash: {db_user['password']}")

    # Test login
    print("Attempting login...")
    response = client.post('/api/login', json={
        "email": test_email,
        "password": test_password
    })
    print(f"Login response: {response.status_code}, {response.json}")
    assert response.status_code == 200

def test_profile_operations(client, auth_headers):
    # Test storing profile
    profile_data = {
        "name": "Test User",
        "age": 25,
        "gender": "male",
        "height": 175,
        "weight": 70,
        "goals": "maintain"
    }
    response = client.post('/api/store-profile', json=profile_data, headers=auth_headers)
    assert response.status_code == 201
    assert "bmi" in response.json
    
    # Test getting profile
    response = client.get('/api/get-profile', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['name'] == "Test User"
    
    # Test editing profile
    response = client.put('/api/edit-profile', json={"name": "Updated Name"}, headers=auth_headers)
    assert response.status_code == 200
    
    # Verify update
    response = client.get('/api/get-profile', headers=auth_headers)
    assert response.json['name'] == "Updated Name"

def test_sleep_endpoints(client, auth_headers):
    # Test logging sleep
    sleep_data = {
        "sleep_hours": 7.5,
        "sleep_rating": 4
    }
    response = client.post('/api/log-sleep', json=sleep_data, headers=auth_headers)
    assert response.status_code == 201
    
    # Test getting sleep history
    response = client.get('/api/sleep-history', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json['history']) == 1
    
    # Test sleep streak
    response = client.get('/api/sleep-streak', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['streak'] >= 1

def test_steps_endpoints(client, auth_headers):
    # Test updating steps
    response = client.post('/api/update-steps', json={"steps": 5000}, headers=auth_headers)
    assert response.status_code == 200
    
    # Test getting steps
    response = client.get('/api/get-steps', headers=auth_headers)
    assert response.status_code == 200
    assert "steps" in response.json
    
    # Test step history
    response = client.get('/api/get-step-history', headers=auth_headers)
    assert response.status_code == 200
    assert "daily" in response.json

def test_challenges(client, auth_headers):
    # Add a test challenge
    test_challenge = {
        "name": "Test Challenge",
        "description": "Test Description",
        "target": 10,
        "unit": "tests"
    }
    client.post('/api/add-challenge', json=test_challenge, headers=auth_headers)
    
    # Test getting challenges
    response = client.get('/api/get-challenges', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json['challenges']) > 0
    
    # Test joining challenge
    response = client.post('/api/join-challenge', json={"challenge_name": "Test Challenge"}, headers=auth_headers)
    assert response.status_code == 201
    
    # Test updating progress
    response = client.post('/api/update-challenge-progress', json={
        "challenge_name": "Test Challenge",
        "progress": 5
    }, headers=auth_headers)
    assert response.status_code == 200
    
    # Test getting user challenges
    response = client.get('/api/get-user-challenges', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json['challenges']) > 0

def test_meal_endpoints(client, auth_headers):
    # Mock food database
    with patch('app.food_database', {
        "Apple": {"Calories (kcal)": 52, "Protein (g)": 0.3, "Carbohydrates (g)": 14, "Fats (g)": 0.2},
        "Chicken Breast": {"Calories (kcal)": 165, "Protein (g)": 31, "Carbohydrates (g)": 0, "Fats (g)": 3.6}
    }):
        # Test logging meal
        response = client.post('/api/log-meal', json={
            "meals": {
                "breakfast": ["Apple"],
                "lunch": ["Chicken Breast"]
            }
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json['total_nutrition']['calories'] > 0
        
        # Test getting meals
        response = client.get('/api/get-meals', headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json['meals']) > 0

def test_groups(client, auth_headers):
    # Test creating group
    response = client.post('/api/create-group', json={"group_name": "Test Group"}, headers=auth_headers)
    assert response.status_code == 201
    
    # Test joining group
    response = client.post('/api/join-group', json={"group_name": "Test Group"}, headers=auth_headers)
    assert response.status_code == 200
    
    # Test posting to group
    response = client.post('/api/group-post', json={
        "group_name": "Test Group",
        "content": "Test post"
    }, headers=auth_headers)
    assert response.status_code == 201
    
    # Test getting group posts
    response = client.get('/api/get-group-posts/Test Group', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json) > 0

def test_forgot_password_flow(client):
    # Register a test user
    test_user = {
        "email": "password@example.com",
        "password": "originalpass"
    }
    client.post('/api/register', json=test_user)
    
    # Test forgot password
    with patch('app.mail.send', MagicMock()):
        response = client.post('/api/forgot-password', json={"email": "password@example.com"})
        assert response.status_code == 200
    
    # Test verify OTP (mock OTP)
    with patch('app.users_collection.find_one', return_value={
        "email": "password@example.com",
        "otp": "123456",
        "otp_expiry": datetime.utcnow() + timedelta(minutes=10),
        "otp_verified": False
    }):
        response = client.post('/api/verify-otp', json={
            "email": "password@example.com",
            "otp": "123456"
        })
        assert response.status_code == 200
    
    # Test reset password
    response = client.post('/api/reset-password', json={
        "email": "password@example.com",
        "password": "newpassword"
    })
    assert response.status_code == 200
    
    # Verify new password works
    response = client.post('/api/login', json={
        "email": "password@example.com",
        "password": "newpassword"
    })
    assert response.status_code == 200

def test_workout_recommendations(client, auth_headers):
    # Need a profile for personalized recommendations
    client.post('/api/store-profile', json={
        "name": "Workout Test",
        "age": 30,
        "gender": "male",
        "height": 180,
        "weight": 75,
        "goals": "maintain"
    }, headers=auth_headers)
    
    # Mock exercises data
    with patch('app.exercises_df', MagicMock()), patch('app.cosine_sim', MagicMock()):
        # Test general recommendations
        response = client.get('/api/get-recommendations', headers=auth_headers)
        assert response.status_code == 200
        
        # Test personalized recommendations
        response = client.get('/api/get-personalized-workouts', headers=auth_headers)
        assert response.status_code == 200

def test_meal_plan(client, auth_headers):
    # Need a profile for meal plan
    client.post('/api/store-profile', json={
        "name": "Meal Test",
        "age": 30,
        "gender": "female",
        "height": 165,
        "weight": 60,
        "goals": "lose_weight"
    }, headers=auth_headers)
    
    # Mock food model and data
    with patch('app.food_model', MagicMock()), patch('app.food_df', MagicMock()):
        response = client.get('/api/meal-plan', headers=auth_headers)
        assert response.status_code == 200

def test_news_endpoint(client):
    with patch('app.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            "articles": [
                {
                    "title": "Test News",
                    "description": "Test Description",
                    "url": "http://example.com",
                    "urlToImage": "http://example.com/image.jpg",
                    "publishedAt": "2023-01-01"
                }
            ]
        }
        mock_get.return_value.raise_for_status.return_value = None
        
        response = client.get('/api/news')
        assert response.status_code == 200
        assert len(response.json) > 0

def test_progress_tracking(client, auth_headers):
    # Test tracking progress
    response = client.post('/api/track-progress', headers=auth_headers)
    assert response.status_code == 200
    
    # Test getting progress
    response = client.get('/api/get-progress', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['completed_days'] > 0
    
    # Test resetting progress
    response = client.post('/api/reset-progress', headers=auth_headers)
    assert response.status_code == 200