import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
import mongomock
import pandas as pd
from unittest.mock import patch

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    app.config['MAIL_SUPPRESS_SEND'] = True  
    
    mock_client = mongomock.MongoClient()
    app.db = mock_client.test_db
    app.users_collection = app.db.users
    app.profiles_collection = app.db.profiles
    app.challenges_collection = app.db.challenges
    app.user_challenges_collection = app.db.user_challenges  
    app.groups_collection = app.db.groups  
    app.sleep_collection = app.db.sleep  
    app.meals_collection = app.db.meals  
    app.posts_collection = app.db.posts  
    
    app.mail = type('Mail', (), {'send': lambda x: True})

    app.food_database = {
        "Apple": {"Calories (kcal)": 52, "Protein (g)": 0.3},
        "Chicken": {"Calories (kcal)": 239, "Protein (g)": 27}
    }

    app.exercises_df = pd.DataFrame([{
        "id": 1, 
        "name": "Push-up", 
        "bodyPart": "chest", 
        "equipment": "body weight"
    }])
    
    with app.app_context():
        JWTManager(app)
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    with app.app_context():
        access_token = create_access_token(identity="test@example.com")
        return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def mock_food_data():
    return {
        "Apple": {"Calories (kcal)": 52, "Protein (g)": 0.3},
        "Chicken": {"Calories (kcal)": 239, "Protein (g)": 27}
    }