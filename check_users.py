from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.HealthFitnessApp

# Check users collection
users = db.users.find()
for user in users:
    print(user)  # Print user details to check password format
