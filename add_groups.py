from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.HealthFitnessApp
groups_collection = db.groups

# Insert groups
groups = [
    {"name": "Fitness Enthusiasts"},
    {"name": "Yoga Lovers"},
    {"name": "Keto Dieters"}
]

groups_collection.insert_many(groups)
print("✅ Groups added successfully!")
