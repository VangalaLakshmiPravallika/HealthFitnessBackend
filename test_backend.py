import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import json
import os
from unittest.mock import patch, MagicMock
import bcrypt
import pyotp
import smtplib
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

@pytest.fixture
def app():
    from app import app  
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    # Register a test user
    test_user = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    client.post('/api/register', json=test_user)
    
    # Login to get token
    response = client.post('/api/login', json=test_user)
    token = response.json['token']
    
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

# Mock MongoDB collections
@pytest.fixture(autouse=True)
def mock_mongo(monkeypatch):
    from pymongo import MongoClient
    from unittest.mock import MagicMock
    
    mock_client = MagicMock(spec=MongoClient)
    mock_db = MagicMock()
    mock_client.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    
    # Mock collections
    collections = {
        'users': MagicMock(),
        'sleep': MagicMock(),
        'achievements': MagicMock(),
        'groups': MagicMock(),
        'meals': MagicMock(),
        'badges': MagicMock(),
        'progress': MagicMock(),
        'steps': MagicMock(),
        'profiles': MagicMock(),
        'challenges': MagicMock(),
        'user_challenges': MagicMock(),
        'notifications': MagicMock(),
        'fitness_assessment': MagicMock()
    }
    
    mock_db.__getitem__.side_effect = lambda name: collections[name]
    
    # Update this line to point to your app module
    monkeypatch.setattr('app.MongoClient', mock_client)
    
    return collections

# Test cases
class TestAuthEndpoints:
    def test_register(self, client, mock_mongo):
        mock_mongo['users'].find_one.return_value = None
        
        response = client.post('/api/register', json={
            "email": "new@example.com",
            "password": "newpassword"
        })
        
        assert response.status_code == 201
        assert response.json['message'] == "User registered successfully!"
        mock_mongo['users'].insert_one.assert_called_once()

    def test_register_existing_user(self, client, mock_mongo):
        mock_mongo['users'].find_one.return_value = {"email": "exists@example.com"}
        
        response = client.post('/api/register', json={
            "email": "exists@example.com",
            "password": "password"
        })
        
        assert response.status_code == 400
        assert "already exists" in response.json['error']

    def test_login_success(self, client, mock_mongo):
        hashed = bcrypt.hashpw(b"testpassword", bcrypt.gensalt())
        mock_mongo['users'].find_one.return_value = {
            "email": "test@example.com",
            "password": hashed
        }
        mock_mongo['profiles'].find_one.return_value = None
        
        response = client.post('/api/login', json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        
        assert response.status_code == 200
        assert "token" in response.json

    def test_login_invalid_credentials(self, client, mock_mongo):
        hashed = bcrypt.hashpw(b"rightpassword", bcrypt.gensalt())
        mock_mongo['users'].find_one.return_value = {
            "email": "test@example.com",
            "password": hashed
        }
        
        response = client.post('/api/login', json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Invalid" in response.json['error']

class TestProfileEndpoints:
    def test_store_profile(self, client, auth_headers, mock_mongo):
        test_profile = {
            "name": "Test User",
            "age": 30,
            "gender": "male",
            "height": 175,
            "weight": 70,
            "goals": "maintain"
        }
        
        response = client.post('/api/store-profile', 
                             json=test_profile,
                             headers=auth_headers)
        
        assert response.status_code == 201
        mock_mongo['profiles'].update_one.assert_called_once()

    def test_get_profile(self, client, auth_headers, mock_mongo):
        mock_profile = {
            "email": "test@example.com",
            "name": "Test User",
            "age": 30,
            "gender": "male",
            "height": 175,
            "weight": 70,
            "bmi": 22.86,
            "daily_calories": 1540,
            "goals": "maintain"
        }
        mock_mongo['profiles'].find_one.return_value = mock_profile
        
        response = client.get('/api/get-profile', headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['name'] == "Test User"
        assert response.json['bmi'] == pytest.approx(22.86, 0.01)

class TestWorkoutEndpoints:
    @patch('app.exercises_df', pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Push-up', 'Squat', 'Lunge'],
        'bodyPart': ['chest', 'legs', 'legs'],
        'equipment': ['body weight', 'body weight', 'body weight'],
        'target': ['pectorals', 'quads', 'glutes'],
        'tags': ['chest body weight pectorals', 'legs body weight quads', 'legs body weight glutes']
    }))
    @patch('app.tfidf_matrix', MagicMock())
    @patch('app.cosine_sim', np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]))
    def test_get_recommendations(self, client, auth_headers, mock_mongo):
        response = client.get('/api/get-recommendations', headers=auth_headers)
        
        assert response.status_code == 200
        assert len(response.json['recommended_workouts']) > 0

    @patch('app.exercises_df', pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Push-up', 'Squat', 'Lunge'],
        'bodyPart': ['chest', 'legs', 'legs'],
        'equipment': ['body weight', 'body weight', 'body weight'],
        'target': ['pectorals', 'quads', 'glutes'],
        'tags': ['chest body weight pectorals', 'legs body weight quads', 'legs body weight glutes']
    }))
    @patch('app.tfidf_matrix', MagicMock())
    @patch('app.cosine_sim', np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]))
    def test_get_personalized_workouts(self, client, auth_headers, mock_mongo):
        mock_mongo['profiles'].find_one.return_value = {
            "email": "test@example.com",
            "bmi": 22.5,
            "preferred_body_part": "legs",
            "equipment": ["body weight"]
        }
        
        response = client.get('/api/get-personalized-workouts', headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['intensity_level'] == "intermediate"

class TestMealEndpoints:
    @patch('app.food_database', {
        "Apple": {"Calories (kcal)": 52, "Protein (g)": 0.3, "Carbohydrates (g)": 14, "Fats (g)": 0.2},
        "Chicken Breast": {"Calories (kcal)": 165, "Protein (g)": 31, "Carbohydrates (g)": 0, "Fats (g)": 3.6}
    })
    @patch('app.food_model', MagicMock(spec=NearestNeighbors))
    @patch('app.food_df', pd.DataFrame({
        'name': ['Apple', 'Chicken Breast'],
        'calories': [52, 165],
        'protein': [0.3, 31],
        'carbs': [14, 0],
        'fat': [0.2, 3.6]
    }))
    def test_log_meal(self, client, auth_headers, mock_mongo):
        meal_data = {
            "meals": {
                "breakfast": ["Apple"],
                "lunch": ["Chicken Breast"]
            }
        }
        
        response = client.post('/api/log-meal', 
                             json=meal_data,
                             headers=auth_headers)
        
        assert response.status_code == 201
        assert response.json['total_nutrition']['calories'] == 217
        mock_mongo['meals'].insert_one.assert_called_once()

    def test_get_meal_plan(self, client, auth_headers, mock_mongo):
        mock_mongo['profiles'].find_one.return_value = {
            "bmi": 22.5,
            "daily_calories": 2000,
            "goals": "maintain"
        }
        
        response = client.get('/api/meal-plan', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'breakfast' in response.json
        assert 'lunch' in response.json
        assert 'dinner' in response.json

class TestChallengeEndpoints:
    def test_get_challenges(self, client, auth_headers, mock_mongo):
        mock_mongo['challenges'].find.return_value = [
            {"name": "10k Steps", "description": "Walk 10,000 steps", "target": 10000, "unit": "steps"}
        ]
        
        response = client.get('/api/get-challenges', headers=auth_headers)
        
        assert response.status_code == 200
        assert len(response.json['challenges']) == 1

    def test_join_challenge(self, client, auth_headers, mock_mongo):
        mock_mongo['challenges'].find_one.return_value = {
            "name": "10k Steps",
            "description": "Walk 10,000 steps",
            "target": 10000,
            "unit": "steps"
        }
        mock_mongo['user_challenges'].find_one.return_value = None
        
        response = client.post('/api/join-challenge', 
                             json={"challenge_name": "10k Steps"},
                             headers=auth_headers)
        
        assert response.status_code == 201
        mock_mongo['user_challenges'].insert_one.assert_called_once()

class TestSleepEndpoints:
    def test_log_sleep(self, client, auth_headers, mock_mongo):
        sleep_data = {
            "sleep_hours": 7.5,
            "sleep_rating": 4
        }
        
        response = client.post('/api/log-sleep', 
                             json=sleep_data,
                             headers=auth_headers)
        
        assert response.status_code == 201
        mock_mongo['sleep'].insert_one.assert_called_once()

    def test_get_sleep_history(self, client, auth_headers, mock_mongo):
        mock_mongo['sleep'].find.return_value = [
            {"date": "2023-01-01", "sleep_hours": 7.5, "sleep_rating": 4},
            {"date": "2023-01-02", "sleep_hours": 6.5, "sleep_rating": 3}
        ]
        
        response = client.get('/api/sleep-history', headers=auth_headers)
        
        assert response.status_code == 200
        assert len(response.json['history']) == 2
        assert 'sleep_quality' in response.json

class TestGroupEndpoints:
    def test_create_group(self, client, auth_headers, mock_mongo):
        mock_mongo['groups'].find_one.return_value = None
        
        response = client.post('/api/create-group', 
                             json={"group_name": "Test Group"},
                             headers=auth_headers)
        
        assert response.status_code == 201
        mock_mongo['groups'].insert_one.assert_called_once()

    def test_join_group(self, client, auth_headers, mock_mongo):
        mock_mongo['groups'].find_one.return_value = {
            "name": "Existing Group",
            "members": []
        }
        
        response = client.post('/api/join-group', 
                             json={"group_name": "Existing Group"},
                             headers=auth_headers)
        
        assert response.status_code == 200
        mock_mongo['groups'].update_one.assert_called_once()

class TestForgotPassword:
    @patch('app.mail.send', MagicMock())
    def test_forgot_password(self, client, mock_mongo):
        mock_mongo['users'].find_one.return_value = {"email": "test@example.com"}
        
        response = client.post('/forgot-password', json={"email": "test@example.com"})
        
        assert response.status_code == 200
        mock_mongo['users'].update_one.assert_called_once()

    def test_verify_otp(self, client, mock_mongo):
        mock_mongo['users'].find_one.return_value = {
            "email": "test@example.com",
            "otp": "123456",
            "otp_expiry": datetime.utcnow() + timedelta(minutes=10)
        }
        
        response = client.post('/verify-otp', json={
            "email": "test@example.com",
            "otp": "123456"
        })
        
        assert response.status_code == 200
        mock_mongo['users'].update_one.assert_called_once()

    def test_reset_password(self, client, mock_mongo):
        mock_mongo['users'].find_one.return_value = {
            "email": "test@example.com",
            "otp_verified": True
        }
        
        response = client.post('/reset-password', json={
            "email": "test@example.com",
            "password": "newpassword"
        })
        
        assert response.status_code == 200
        mock_mongo['users'].update_one.assert_called_once()

class TestStepsTracking:
    def test_update_steps(self, client, auth_headers, mock_mongo):
        response = client.post('/api/update-steps', 
                             json={"steps": 5000},
                             headers=auth_headers)
        
        assert response.status_code == 200
        mock_mongo['steps'].update_one.assert_called_once()

    def test_get_step_history(self, client, auth_headers, mock_mongo):
        mock_mongo['steps'].aggregate.return_value = [
            {"_id": None, "total": 35000}
        ]
        mock_mongo['steps'].find_one.return_value = {"steps": 5000}
        
        response = client.get('/api/get-step-history', headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['daily'] == 5000
        assert response.json['weekly'] == 35000

class TestProgressTracking:
    def test_track_progress(self, client, auth_headers, mock_mongo):
        mock_mongo['progress'].find_one.return_value = {"completed_days": 2}
        
        response = client.post('/api/track-progress', headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['completed_days'] == 3
        mock_mongo['progress'].update_one.assert_called_once()

    def test_get_progress(self, client, auth_headers, mock_mongo):
        mock_mongo['progress'].find_one.return_value = {
            "completed_days": 3,
            "badge": "Beginner"
        }
        
        response = client.get('/api/get-progress', headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['completed_days'] == 3

class TestFitnessAssessment:
    def test_fitness_assessment(self, client, auth_headers, mock_mongo):
        assessment_data = {
            "pushups": 15,
            "squats": 20,
            "plank_seconds": 30
        }
        
        response = client.post('/api/fitness-assessment', 
                             json=assessment_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        assert "Intermediate" in response.json['fitness_level']
        mock_mongo['fitness_assessment'].update_one.assert_called_once()

class TestNewsEndpoint:
    @patch('app.requests.get')
    def test_get_news(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "Test News",
                    "description": "Test Description",
                    "url": "http://example.com",
                    "urlToImage": "http://example.com/image.jpg",
                    "publishedAt": "2023-01-01T00:00:00Z"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        response = client.get('/api/news')
        
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['title'] == "Test News"