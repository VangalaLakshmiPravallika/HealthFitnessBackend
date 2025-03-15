import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from .env
load_dotenv()

# Verify if the variables are loaded correctly
print("MONGO_URI:", os.getenv("MONGO_URI"))
print("JWT_SECRET_KEY:", os.getenv("JWT_SECRET_KEY"))

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["HealthFitnessDB"]

# Collections
users_collection = db["users"]
sleep_collection = db["sleep"]
achievements_collection = db["achievements"]
groups_collection = db["groups"]
notifications_collection = db["notifications"]
