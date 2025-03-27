import unittest
import requests
import json
import os
from datetime import datetime, timedelta

BASE_URL = "https://healthfitnessbackend.onrender.com/api"  

class TestHealthFitnessApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Register a test user before running tests"""
        cls.test_email = f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
        cls.test_password = "Test@1234"
        
        # Register test user
        register_data = {
            "email": cls.test_email,
            "password": cls.test_password
        }
        response = requests.post(f"{BASE_URL}/register", json=register_data)
        cls.assertEqual(response.status_code, 201)
        
        # Store auth token for subsequent requests
        login_data = {
            "email": cls.test_email,
            "password": cls.test_password
        }
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        cls.assertEqual(response.status_code, 200)
        cls.auth_token = response.json().get("token")
        cls.headers = {"Authorization": f"Bearer {cls.auth_token}"}
        
        # Create a test profile
        profile_data = {
            "name": "Test User",
            "age": 25,
            "gender": "male",
            "height": 175,
            "weight": 70,
            "goals": "maintain"
        }
        response = requests.post(
            f"{BASE_URL}/store-profile", 
            json=profile_data,
            headers=cls.headers
        )
        cls.assertEqual(response.status_code, 201)

    def test_1_login(self):
        """Test login functionality"""
        # Test successful login
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())
        
        # Test invalid credentials
        invalid_data = {
            "email": self.test_email,
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/login", json=invalid_data)
        self.assertEqual(response.status_code, 401)
    
    def test_2_challenges(self):
        """Test challenge-related endpoints"""
        # Get available challenges
        response = requests.get(f"{BASE_URL}/get-challenges", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        challenges = response.json().get("challenges")
        self.assertGreater(len(challenges), 0)
        
        # Join a challenge
        challenge_name = challenges[0]["name"]
        join_data = {"challenge_name": challenge_name}
        response = requests.post(
            f"{BASE_URL}/join-challenge", 
            json=join_data,
            headers=self.headers
        )
        self.assertIn(response.status_code, [200, 201])
        
        # Get user challenges
        response = requests.get(
            f"{BASE_URL}/get-user-challenges",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        user_challenges = response.json().get("challenges")
        self.assertGreater(len(user_challenges), 0)
        
        # Update challenge progress
        progress_data = {
            "challenge_name": challenge_name,
            "progress": 1000  # Example: 1000 steps
        }
        response = requests.post(
            f"{BASE_URL}/update-challenge-progress",
            json=progress_data,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Get leaderboard
        response = requests.get(
            f"{BASE_URL}/get-leaderboard/{challenge_name}",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("leaderboard", response.json())
    
    def test_3_log_sleep(self):
        """Test sleep logging functionality"""
        # Log sleep data
        sleep_data = {
            "sleep_hours": 7.5,
            "sleep_rating": 4,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        response = requests.post(
            f"{BASE_URL}/log-sleep",
            json=sleep_data,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 201)
        
        # Get sleep history
        response = requests.get(
            f"{BASE_URL}/sleep-history",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        sleep_history = response.json().get("history")
        self.assertGreater(len(sleep_history), 0)
        
        # Test sleep streak calculation
        response = requests.get(
            f"{BASE_URL}/sleep-streak",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("streak", response.json())
    
    def test_4_workout(self):
        """Test workout-related endpoints"""
        # Get workout plan based on BMI
        response = requests.get(
            f"{BASE_URL}/workout-plan",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        workout_plan = response.json().get("workout_plan")
        self.assertGreater(len(workout_plan), 0)
        
        # Get general workout recommendations
        response = requests.get(
            f"{BASE_URL}/get-recommendations",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        recommendations = response.json().get("recommended_workouts")
        self.assertGreater(len(recommendations), 0)
        
        # Get personalized workouts
        response = requests.get(
            f"{BASE_URL}/get-personalized-workouts",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        personalized = response.json().get("recommended_workouts")
        self.assertGreater(len(personalized), 0)
        
        # Track workout progress
        response = requests.post(
            f"{BASE_URL}/track-progress",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("completed_days", response.json())
    
    def test_5_meal(self):
        """Test meal-related endpoints"""
        # Get food items
        response = requests.get(
            f"{BASE_URL}/get-food-items",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        food_items = response.json().get("food_items")
        self.assertGreater(len(food_items), 0)
        
        # Log a meal
        meal_data = {
            "meals": {
                "breakfast": ["Oatmeal", "Banana"],
                "lunch": ["Grilled Chicken", "Brown Rice"],
                "dinner": ["Salmon", "Broccoli"]
            }
        }
        response = requests.post(
            f"{BASE_URL}/log-meal",
            json=meal_data,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("total_nutrition", response.json())
        
        # Get meal history
        response = requests.get(
            f"{BASE_URL}/get-meals",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        meals = response.json().get("meals")
        self.assertGreater(len(meals), 0)
        
        # Get meal plan recommendation
        response = requests.get(
            f"{BASE_URL}/meal-plan",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        meal_plan = response.json()
        self.assertIn("breakfast", meal_plan)
        self.assertIn("lunch", meal_plan)
        self.assertIn("dinner", meal_plan)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test data"""
        pass

if __name__ == "__main__":
    unittest.main()