import pytest
from app import app as flask_app
from pymongo import MongoClient
from mongomock import MongoClient as MockMongoClient
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app import app as flask_app

load_dotenv('.env.test')

@pytest.fixture
def app():
    # Configure test settings
    flask_app.config.update({
        "TESTING": True,
        "JWT_SECRET_KEY": "test-secret-key",
        "MONGO_URI": os.getenv("MONGO_URI"),
        "MAIL_SUPPRESS_SEND": True  # Disable actual email sending
    })
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth(client):
    class Auth:
        def login(self, email="test@example.com", password="test123"):
            # Register if not exists
            client.post('/api/register', 
                      json={"email": email, "password": password})
            # Login
            response = client.post('/api/login',
                                json={"email": email, "password": password})
            return response.json["token"]
    return Auth()

@pytest.fixture(autouse=True)
def setup_teardown_db(app, request):
    if 'integration' in request.keywords:
        # Real Atlas DB with test prefix
        client = MongoClient(app.config["MONGO_URI"])
        db = client.get_database()
        
        # Setup test collections with prefix
        test_collections = {
            "test_users": [],
            "test_profiles": [],
            # Add other collections
        }
        
        # Clean and setup test data
        for coll_name, test_data in test_collections.items():
            if coll_name in db.list_collection_names():
                db[coll_name].delete_many({})
            if test_data:
                db[coll_name].insert_many(test_data)
        
        yield
        
        # Cleanup
        for coll_name in test_collections:
            if coll_name in db.list_collection_names():
                db[coll_name].delete_many({})
    else:
        # Mock DB for unit tests
        app.mongo_client = MockMongoClient()
        yield