import unittest
from pymongo import MongoClient
import os
from dotenv import load_dotenv

class TestGroupsCollection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()
        # Use a TEST database (not production)
        cls.client = MongoClient(os.getenv("MONGO_URI"))
        cls.db = cls.client.TestHealthFitnessApp  # Different DB for testing
        cls.groups_collection = cls.db.groups

    def test_insert_groups(self):
        # Clear old test data
        self.groups_collection.delete_many({})

        # Insert test data
        groups = [
            {"name": "Fitness Enthusiasts"},
            {"name": "Yoga Lovers"},
            {"name": "Keto Dieters"}
        ]
        result = self.groups_collection.insert_many(groups)
        
        # Assertions (checks if test passed)
        self.assertEqual(len(result.inserted_ids), 3)
        self.assertEqual(self.groups_collection.count_documents({}), 3)

    @classmethod
    def tearDownClass(cls):
        # Clean up test database
        cls.groups_collection.delete_many({})
        cls.client.close()

if __name__ == "__main__":
    unittest.main()