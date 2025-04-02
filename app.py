import os
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import logging
import requests
from datetime import datetime
from datetime import datetime, timedelta
import pyotp
import smtplib
import joblib
import sys
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import random
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash


print("✅ Flask is using Python:", sys.executable)

try:
    import sklearn
    print("✅ scikit-learn is installed:", sklearn.__version__)
except ImportError:
    print("❌ ERROR: scikit-learn is NOT available in this environment!")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")  
NEWS_API_URL = "https://newsapi.org/v2/everything"

load_dotenv()

app=Flask(__name__)
CORS(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pravalliva11@gmail.com'
app.config['MAIL_PASSWORD'] = 'tfjl qgmo ybrq kyuz'
app.config['MAIL_DEFAULT_SENDER'] = 'pravalliva11@gmail.com'

mail = Mail(app)
OTP_EXPIRY_MINUTES = 10
bcrypt = Bcrypt(app)


MONGO_URI=os.getenv("MONGO_URI")
client=MongoClient(MONGO_URI)
db = client.HealthFitnessApp
users_collection=db.users
sleep_collection=db.sleep
achievements_collection=db.achievements
groups_collection=db.groups
meal_collection=db.meals
badges_collection=db.badges
progress_collection=db.progress
steps_collection = db.steps
users_collection = db.users
profiles_collection = db.profiles
challenges_collection = db.challenges
user_challenges_collection = db.user_challenges
notifications_collection = db.notifications

app.config["JWT_SECRET_KEY"]=os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

MODEL_PATH = os.path.join(os.getcwd(), "diet_kmeans.pkl")

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import jsonify
from pymongo import MongoClient

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        email = data.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = users_collection.find_one({'email': email})
        if not user:
            return jsonify({'error': 'User not found'}), 404

        otp = str(random.randint(100000, 999999))
        expiry_time = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        users_collection.update_one(
            {'email': email},
            {'$set': {
                'otp': otp,
                'otp_expiry': expiry_time,
                'otp_verified': False
            }}
        )

        msg = Message(
            subject="Password Reset OTP",
            recipients=[email],
            body=f"Your OTP for password reset is: {otp}. It is valid for {OTP_EXPIRY_MINUTES} minutes."
        )

        with app.app_context():
            mail.send(msg)
        
        return jsonify({'message': 'OTP sent to email'}), 200

    except Exception as e:
        return jsonify({'error': f"Error processing request: {str(e)}"}), 500

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        email = data.get('email')
        otp = data.get('otp')

        if not email or not otp:
            return jsonify({'error': 'Email and OTP are required'}), 400

        user = users_collection.find_one({'email': email})
        if not user or not user.get('otp'):
            return jsonify({'error': 'OTP not found for this email'}), 404

        if datetime.utcnow() > user['otp_expiry']:
            users_collection.update_one(
                {'email': email},
                {'$unset': {'otp': '', 'otp_expiry': '', 'otp_verified': ''}}
            )
            return jsonify({'error': 'OTP has expired'}), 400

        if user['otp'] != otp:
            return jsonify({'error': 'Invalid OTP'}), 400

        users_collection.update_one(
            {'email': email},
            {'$set': {'otp_verified': True}}
        )

        return jsonify({'message': 'OTP verified successfully'}), 200

    except Exception as e:
        return jsonify({'error': f"Error verifying OTP: {str(e)}"}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        email = data.get('email')
        new_password = data.get('password')

        if not email or not new_password:
            return jsonify({'error': 'Email and password are required'}), 400

        user = users_collection.find_one({'email': email})
        if not user or not user.get('otp_verified'):
            return jsonify({'error': 'OTP verification required'}), 403

        if isinstance(new_password, str):
            new_password = new_password.encode('utf-8')
        
        hashed_password = bcrypt.generate_password_hash(new_password)
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode('utf-8')

        result = users_collection.update_one(
            {'email': email},
            {
                '$set': {'password': hashed_password},
                '$unset': {'otp': '', 'otp_expiry': '', 'otp_verified': ''}
            }
        )

        if result.modified_count == 0:
            return jsonify({'error': 'Password update failed'}), 500

        return jsonify({'message': 'Password reset successfully'}), 200

    except Exception as e:
        return jsonify({'error': f"Error resetting password: {str(e)}"}), 500


exercises_df = pd.read_csv('fitness_exercises.csv')  
exercises_df['tags'] = exercises_df['bodyPart'] + ' ' + exercises_df['equipment'] + ' ' + exercises_df['target']

tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(exercises_df['tags'])

cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

def get_intensity_level(bmi):
    if bmi < 18.5: return 'beginner'
    elif 18.5 <= bmi < 25: return 'intermediate'
    elif 25 <= bmi < 30: return 'advanced'
    else: return 'low-impact'

def format_gif_url(exercise_id):
    try:
        exercise_id = str(int(exercise_id)).zfill(4)  
        return f"https://d205bpvrqc9yn1.cloudfront.net/{exercise_id}.gif"
    except:
        return None

def create_weekly_workout_plan(filtered_exercises, intensity, workout_history=None):
    # Define workout splits based on intensity
    if intensity == 'beginner':
        splits = {
            'Monday': {'bodyPart': 'cardio', 'count': 3},
            'Wednesday': {'bodyPart': 'full body', 'count': 4},
            'Friday': {'bodyPart': 'full body', 'count': 4}
        }
    elif intensity == 'intermediate':
        splits = {
            'Monday': {'bodyPart': 'upper arms', 'count': 3},
            'Tuesday': {'bodyPart': 'cardio', 'count': 2},
            'Wednesday': {'bodyPart': 'lower legs', 'count': 3},
            'Thursday': {'bodyPart': 'back', 'count': 3},
            'Friday': {'bodyPart': 'chest', 'count': 3},
            'Saturday': {'bodyPart': 'cardio', 'count': 2}
        }
    else:  # advanced or low-impact
        splits = {
            'Monday': {'bodyPart': 'upper arms|lower arms', 'count': 4},
            'Tuesday': {'bodyPart': 'cardio', 'count': 3},
            'Wednesday': {'bodyPart': 'upper legs|lower legs', 'count': 4},
            'Thursday': {'bodyPart': 'back|waist', 'count': 4},
            'Friday': {'bodyPart': 'chest|shoulders', 'count': 4},
            'Saturday': {'bodyPart': 'cardio', 'count': 3}
        }
    
    weekly_plan = {}
    
    for day, params in splits.items():
        # Filter exercises for the target body part
        day_exercises = filtered_exercises[filtered_exercises['bodyPart'].str.contains(params['bodyPart'], case=False, regex=True)]
        
        # If no exercises found for the specific body part, fall back to similar ones
        if len(day_exercises) == 0:
            similar_body_parts = {
                'upper arms': 'arms',
                'lower legs': 'legs',
                'back': 'waist',
                'chest': 'shoulders'
            }
            for original, fallback in similar_body_parts.items():
                if original in params['bodyPart']:
                    day_exercises = filtered_exercises[filtered_exercises['bodyPart'].str.contains(fallback, case=False)]
                    break
        
        # If we still have no exercises, get random ones
        if len(day_exercises) == 0:
            day_exercises = filtered_exercises
        
        # Sample the required number of exercises
        sample_size = min(params['count'], len(day_exercises))
        if workout_history:
            try:
                # Try to get exercises not recently done
                recent_exercises = set([ex['exerciseId'] for ex in workout_history[-5:]])  # last 5 workouts
                new_exercises = day_exercises[~day_exercises['id'].isin(recent_exercises)]
                if len(new_exercises) >= sample_size:
                    selected = new_exercises.sample(sample_size)
                else:
                    selected = day_exercises.sample(sample_size)
            except:
                selected = day_exercises.sample(sample_size)
        else:
            selected = day_exercises.sample(sample_size)
        
        # Format the exercises
        selected = selected.copy()
        selected['gifUrl'] = selected['id'].apply(format_gif_url)
        weekly_plan[day] = selected.replace({pd.NA: None}).to_dict('records')
    
    return weekly_plan

@app.route("/api/get-personalized-weekly-plan", methods=["GET"])
@jwt_required()
def get_personalized_weekly_plan():
    """Personalized weekly workout plan based on user profile"""
    try:
        if exercises_df.empty or cosine_sim is None:
            raise Exception("Exercise data not loaded")
            
        user_email = get_jwt_identity()
        user = profiles_collection.find_one({"email": user_email})
        
        if not user or "bmi" not in user:
            return jsonify({
                "success": False,
                "error": "BMI not found. Please update your profile."
            }), 400
        
        bmi = user["bmi"]
        intensity = get_intensity_level(bmi)
        preferred_body_part = user.get("preferred_body_part", "all")
        equipment_available = user.get("equipment", ["body weight"])
        workout_history = user.get("workout_history", [])
        
        # Filter exercises based on user profile
        filtered_exercises = exercises_df.copy()
        
        if intensity == 'beginner':
            filtered_exercises = filtered_exercises[~filtered_exercises['name'].str.contains('advanced|pro', case=False)]
        elif intensity == 'low-impact':
            filtered_exercises = filtered_exercises[filtered_exercises['equipment'].str.contains('body weight|resistance band', case=False)]
        
        if preferred_body_part != "all":
            # Boost preferred body part exercises by including them more often
            preferred_exercises = filtered_exercises[filtered_exercises['bodyPart'] == preferred_body_part]
            other_exercises = filtered_exercises[filtered_exercises['bodyPart'] != preferred_body_part]
            filtered_exercises = pd.concat([preferred_exercises, preferred_exercises, other_exercises])
        
        filtered_exercises = filtered_exercises[filtered_exercises['equipment'].isin(equipment_available)]
        
        # Create weekly plan
        weekly_plan = create_weekly_workout_plan(filtered_exercises, intensity, workout_history)
        
        return jsonify({
            "success": True,
            "bmi": bmi,
            "intensity_level": intensity,
            "weekly_workout_plan": weekly_plan
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def load_food_data():
    try:
        file_path = os.path.join(os.getcwd(), "food_database.xlsx")
        print(f"📂 Checking file at: {file_path}")  
        if not os.path.exists(file_path):
            print("❌ File not found!")
            return {}

        df = pd.read_excel(file_path, engine="openpyxl")
        print("✅ First 5 rows of DataFrame:")
        print(df.head())  
        required_columns = ["Food Name", "Calories (kcal)", "Protein (g)", "Carbohydrates (g)", "Fats (g)"]
        for col in required_columns:
            if col not in df.columns:
                print(f"❌ Column '{col}' not found in Excel!")
                return {}

        
        df = df.fillna(0)
        numeric_columns = ["Calories (kcal)", "Protein (g)", "Carbohydrates (g)", "Fats (g)"]
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce").fillna(0)

       
        food_dict = df.set_index("Food Name")[numeric_columns].to_dict(orient="index")

        print(f"✅ Loaded Food Items: {list(food_dict.keys())}") 
        return food_dict

    except Exception as e:
        print(f"⚠ Error loading food database: {e}")
        return {}

food_database = load_food_data()
    

def initialize_model():
    try:
        if not food_database:
            print("⚠ Food database not loaded - cannot initialize model")
            return None, None
        
        foods = []
        for name, nutrients in food_database.items():
            foods.append({
                'name': name,
                'calories': nutrients['Calories (kcal)'],
                'protein': nutrients['Protein (g)'],
                'carbs': nutrients['Carbohydrates (g)'],
                'fat': nutrients['Fats (g)']
            })
        
        food_df = pd.DataFrame(foods)
        features = food_df[['calories', 'protein', 'carbs', 'fat']]
        model = NearestNeighbors(n_neighbors=5, algorithm='ball_tree')
        model.fit(features)
        return model, food_df
    except Exception as e:
        print(f"⚠ Error initializing model: {e}")
        return None, None
    
food_model, food_df = initialize_model()

def calculate_calorie_needs(bmi, weight_kg, activity_level):
    base_calories = weight_kg * 22 
    activity_multiplier = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }.get(activity_level, 1.2)
    
    if bmi < 18.5:
        return base_calories * activity_multiplier * 1.1 
    elif bmi > 25:
        return base_calories * activity_multiplier * 0.9  
    else:
        return base_calories * activity_multiplier  

def generate_meal_plan(bmi, daily_calories):
    if not food_model or food_df.empty:
        raise ValueError("Food database not initialized")
    
    macros = get_macros_by_bmi(bmi)
    
    
    meals = {
        'breakfast': generate_meal(daily_calories * 0.25, macros),
        'lunch': generate_meal(daily_calories * 0.35, macros),
        'dinner': generate_meal(daily_calories * 0.30, macros),
        'snacks': [
            generate_meal(daily_calories * 0.05, macros),
            generate_meal(daily_calories * 0.05, macros)
        ]
    }
    
    meals['total_calories'] = sum(
        meal['total_calories'] 
        for meal in meals.values() 
        if isinstance(meal, dict)
    )
    
    return meals

def get_macros_by_bmi(bmi):
    """Determine macronutrient ratios based on BMI"""
    if bmi < 18.5:  
        return {'protein': 0.25, 'carbs': 0.50, 'fat': 0.25}
    elif bmi > 25:  
        return {'protein': 0.35, 'carbs': 0.40, 'fat': 0.25}
    else: 
        return {'protein': 0.30, 'carbs': 0.45, 'fat': 0.25}

def generate_meal(calories, macros):
    target_protein = calories * macros['protein'] / 4  
    target_carbs = calories * macros['carbs'] / 4     
    target_fat = calories * macros['fat'] / 9         
    
    target_vector = [calories, target_protein, target_carbs, target_fat]
    distances, indices = food_model.kneighbors([target_vector])
    
    selected_indices = random.sample(list(indices[0]), min(3, len(indices[0])))
    meal_foods = food_df.iloc[selected_indices].to_dict('records')
    
    return {
        'foods': [{
            'name': food['name'],
            'calories': food['calories'],
            'protein': food['protein'],
            'carbs': food['carbs'],
            'fat': food['fat']
        } for food in meal_foods],
        'total_calories': sum(f['calories'] for f in meal_foods),
        'total_protein': sum(f['protein'] for f in meal_foods),
        'total_carbs': sum(f['carbs'] for f in meal_foods),
        'total_fat': sum(f['fat'] for f in meal_foods)
    }

@app.route('/api/meal-plan', methods=['GET'])
@jwt_required()
def get_meal_plan():
    try:
        user_email = get_jwt_identity()
        profile = profiles_collection.find_one(
            {"email": user_email},
            {"_id": 0, "bmi": 1, "daily_calories": 1, "goals": 1}
        )
        
        if not profile:
            return jsonify({"error": "Profile not found. Please complete your profile first."}), 404
            
        if 'bmi' not in profile or 'daily_calories' not in profile:
            return jsonify({"error": "Incomplete profile data"}), 400
            
        daily_calories = adjust_calories_by_goal(
            profile['daily_calories'],
            profile.get('goals', 'maintain'),
            profile['bmi']
        )
        
        meal_plan = generate_meal_plan(
            bmi=profile['bmi'],
            daily_calories=daily_calories
        )
        
        if not meal_plan:
            return jsonify({"error": "Failed to generate meal plan"}), 500
            
        return jsonify(meal_plan)
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

def adjust_calories_by_goal(base_calories, goal, bmi):
    if goal == "lose_weight" or bmi > 25:
        return base_calories * 0.9  
    elif goal == "gain_weight" or bmi < 18.5:
        return base_calories * 1.1  
    return base_calories 

kmeans = None
try:
    if os.path.exists(MODEL_PATH):
        print("🔍 Loading model from:", MODEL_PATH)
        kmeans = joblib.load(MODEL_PATH)
        print("✅ Model loaded successfully!")
    else:
        print("❌ Model file not found!")
except Exception as e:
    print(f"❌ ERROR: Model could not be loaded: {e}")

def calculate_bmi(weight_kg, height_cm):
    if height_cm <= 0 or weight_kg <= 0:
        return None, "Invalid input"

    height_m = height_cm / 100  
    bmi = round(weight_kg / (height_m ** 2), 2) 
    return bmi


default_challenges = [
    {"name": "🏃 10,000 Steps Daily", "description": "Walk 10,000 steps every day", "target": 10000, "unit": "steps"},
    {"name": "💧 Drink 3L Water Daily", "description": "Drink at least 3 liters of water daily", "target": 3, "unit": "liters"},
    {"name": "🏋️ Workout 5 Days a Week", "description": "Complete 5 workouts per week", "target": 5, "unit": "sessions"},
    {"name": "🍎 Eat 5 Servings of Fruits/Veggies", "description": "Eat 5 servings of fruits/veggies daily", "target": 5, "unit": "servings"},
    {"name": "🛌 Sleep 8 Hours Daily", "description": "Get at least 8 hours of sleep daily", "target": 8, "unit": "hours"}
]

if challenges_collection.count_documents({}) == 0:
    challenges_collection.insert_many(default_challenges)

@app.route("/",methods=["GET"])
def home():
    return jsonify({"message": "Flask API is running!"})

@app.route("/api/recommend-diet", methods=["GET"])
@jwt_required()
def recommend_diet():
    import sys
    print(f"✅ Inside API: Flask is using Python: {sys.executable}")

    try:
        import sklearn
        print(f"✅ scikit-learn is installed: {sklearn.__version__}")
    except ImportError as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": "Failed to recommend diet", "details": str(e)}), 500

    user_email = get_jwt_identity()

    try:
        print(f"📩 Fetching user data for: {user_email}")

        user = profiles_collection.find_one({"email": user_email}, {"_id": 0, "bmi": 1})
        if not user or "bmi" not in user:
            print("❌ BMI not found. User must update their profile.")
            return jsonify({"error": "BMI not found. Please update your profile."}), 400

        bmi = user["bmi"]
        print(f"✅ Retrieved BMI: {bmi}")

        meals = list(meal_collection.find({"user": user_email}, {"_id": 0}))
        if not meals:
            print("⚠ No meal data found for user.")
            return jsonify({"message": "No meal data available"}), 400

        total_nutrition = {
            "calories": sum(meal.get("nutrition", {}).get("calories", 0) for meal in meals),
            "protein": sum(meal.get("nutrition", {}).get("protein", 0) for meal in meals),
            "carbs": sum(meal.get("nutrition", {}).get("carbs", 0) for meal in meals),
            "fats": sum(meal.get("nutrition", {}).get("fats", 0) for meal in meals),
        }
        print(f"📊 Nutrition Summary: {total_nutrition}")

        model_path = os.path.join(os.getcwd(), "diet_kmeans.pkl")
        if not os.path.exists(model_path):
            print(f"❌ Model file not found at {model_path}")
            return jsonify({"error": "Diet model not available"}), 500

        kmeans_model = joblib.load(model_path)
        print("✅ Model loaded successfully!")

        user_data = [[bmi, 3, 4, 2, 2]]
        print(f"📊 Predicting cluster for input: {user_data}")

        cluster = kmeans_model.predict(user_data)[0]
        print(f"✅ Predicted Cluster: {cluster}")

        diet_plans = {
            0: {
                "goal": "Weight Gain",
                "breakfast": "Avocado Toast & Eggs",
                "lunch": "Chicken & Quinoa",
                "dinner": "Salmon & Brown Rice",
                "snacks": "Greek Yogurt with Nuts"
            },
            1: {
                "goal": "Maintenance",
                "breakfast": "Oats & Banana",
                "lunch": "Grilled Chicken Salad",
                "dinner": "Stir-fry Tofu with Rice",
                "snacks": "Hummus with Carrots"
            },
            2: {
                "goal": "Weight Loss",
                "breakfast": "Scrambled Eggs with Spinach",
                "lunch": "Grilled Fish & Veggies",
                "dinner": "Vegetable Soup",
                "snacks": "Almond Butter & Apple"
            }
        }

        recommended_diet = diet_plans.get(cluster, {"goal": "Balanced Diet", "breakfast": "Smoothie", "lunch": "Quinoa Salad", "dinner": "Grilled Fish"})
        
        return jsonify({
            "bmi": bmi,
            "overall_nutrition": total_nutrition,
            "recommended_diet": recommended_diet
        }), 200

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({"error": "Failed to recommend diet", "details": str(e)}), 500
    

@app.route("/api/get-challenges", methods=["GET"])
@jwt_required()
def get_challenges():
    challenges = list(challenges_collection.find({}, {"_id": 0}))
    return jsonify({"challenges": challenges}), 200

@app.route("/api/news", methods=["GET"])
def get_news():
    try:
        query = "health fitness diet"
        params = {
            "q": query,
            "sortBy": "publishedAt",
            "pageSize": 10,  
            "apiKey": NEWS_API_KEY,
        }

        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()  
        news_data = response.json()

        articles = news_data.get("articles", [])
        news = [
            {
                "title": article.get("title", "No title"),
                "description": article.get("description", "No description"),
                "url": article.get("url", "#"),
                "urlToImage": article.get("urlToImage", ""),
                "publishedAt": article.get("publishedAt", ""),
            }
            for article in articles
        ]

        return jsonify(news)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/join-challenge", methods=["POST"])
@jwt_required()
def join_challenge():
    data = request.json
    user_email = get_jwt_identity()
    challenge_name = data.get("challenge_name")

    if not challenge_name:
        return jsonify({"error": "Challenge name is required"}), 400

    challenge = challenges_collection.find_one({"name": challenge_name})
    if not challenge:
        return jsonify({"error": "Challenge not found"}), 404

    existing_entry = user_challenges_collection.find_one({"email": user_email, "challenge_name": challenge_name})
    if existing_entry:
        return jsonify({"message": "You have already joined this challenge"}), 200

    user_challenges_collection.insert_one({
        "email": user_email,
        "challenge_name": challenge_name,
        "progress": 0,
        "target": challenge["target"],
        "unit": challenge["unit"],
        "joined_at": datetime.utcnow()
    })

    return jsonify({"message": f"Joined challenge: {challenge_name}"}), 201


@app.route("/api/update-challenge-progress", methods=["POST"])
@jwt_required()
def update_challenge_progress():
    data = request.json
    user_email = get_jwt_identity()
    challenge_name = data.get("challenge_name")
    progress = data.get("progress")

    if not challenge_name or progress is None:
        return jsonify({"error": "Challenge name and progress are required"}), 400

    challenge = challenges_collection.find_one({"name": challenge_name})
    if not challenge:
        return jsonify({"error": "Challenge not found"}), 404

    user_progress = user_challenges_collection.find_one({"email": user_email, "challenge_name": challenge_name})
    if not user_progress:
        return jsonify({"error": "You have not joined this challenge"}), 403

    new_progress = user_progress["progress"] + progress
    is_completed = new_progress >= challenge["target"]

    user_challenges_collection.update_one(
        {"email": user_email, "challenge_name": challenge_name},
        {"$set": {"progress": new_progress, "completed": is_completed}}
    )

    if is_completed:
        badge_title = f"🏆 {challenge_name} Champion"
        badge_description = f"Congratulations! You completed the '{challenge_name}' challenge and earned the {badge_title} badge!"

        achievements_collection.insert_one({
            "user": user_email,
            "title": badge_title,
            "description": badge_description,
            "likes": 0,
            "comments": [],
            "date": datetime.utcnow().strftime("%Y-%m-%d")
        })

        return jsonify({
            "message": f"Congratulations! You completed '{challenge_name}' 🎉",
            "badge": badge_title
        }), 200

    return jsonify({"message": "Progress updated successfully!", "new_progress": new_progress}), 200


@app.route("/api/reset-challenge-progress", methods=["POST"])
@jwt_required()
def reset_challenge_progress():
    data = request.json
    user_email = get_jwt_identity()
    challenge_name = data.get("challenge_name")

    if not challenge_name:
        return jsonify({"error": "Challenge name is required"}), 400

    result = user_challenges_collection.update_one(
        {"email": user_email, "challenge_name": challenge_name},
        {"$set": {"progress": 0, "completed": False}}
    )

    if result.modified_count > 0:
        return jsonify({"message": f"Progress for '{challenge_name}' has been reset!"}), 200

    return jsonify({"error": "Challenge progress not found"}), 404

@app.route("/api/get-user-challenges", methods=["GET"])
@jwt_required()
def get_user_challenges():
    user_email = get_jwt_identity()
    user_challenges = list(user_challenges_collection.find({"email": user_email}, {"_id": 0}))

    return jsonify({"challenges": user_challenges}), 200

@app.route("/api/get-leaderboard/<challenge_name>", methods=["GET"])
@jwt_required()
def get_leaderboard(challenge_name):
    try:
        # Get all entries for this challenge
        leaderboard = list(user_challenges_collection.find(
            {"challenge_name": challenge_name}, 
            {"_id": 0, "email": 1, "progress": 1}
        ))

        if not leaderboard:
            return jsonify({"message": "No entries found for this challenge", "leaderboard": []}), 200

        # Sort by progress (descending)
        leaderboard_sorted = sorted(leaderboard, key=lambda x: x["progress"], reverse=True)

        # Add usernames
        for entry in leaderboard_sorted:
            user = users_collection.find_one(
                {"email": entry["email"]}, 
                {"_id": 0, "username": 1}
            )
            entry["username"] = user.get("username", entry["email"]) if user else entry["email"]
            # Remove email if you want to keep it private
            del entry["email"]

        return jsonify({"leaderboard": leaderboard_sorted}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/leave-challenge", methods=["POST"])
@jwt_required()
def leave_challenge():
    data = request.json
    user_email = get_jwt_identity()
    challenge_name = data.get("challenge_name")

    if not challenge_name:
        return jsonify({"error": "Challenge name is required"}), 400

    result = user_challenges_collection.delete_one({"email": user_email, "challenge_name": challenge_name})

    if result.deleted_count > 0:
        return jsonify({"message": f"You have left the '{challenge_name}' challenge."}), 200

    return jsonify({"error": "Challenge not found or not joined."}), 404


@app.route("/api/add-challenge", methods=["POST"])
@jwt_required()
def add_challenge():
    data = request.json
    challenge_name = data.get("name")
    description = data.get("description")
    target = data.get("target")
    unit = data.get("unit")

    if not all([challenge_name, description, target, unit]):
        return jsonify({"error": "All fields (name, description, target, unit) are required"}), 400

    if challenges_collection.find_one({"name": challenge_name}):
        return jsonify({"error": "Challenge already exists"}), 400

    new_challenge = {
        "name": challenge_name,
        "description": description,
        "target": target,
        "unit": unit
    }

    challenges_collection.insert_one(new_challenge)

    return jsonify({"message": "New challenge added!", "challenge": new_challenge}), 2011

@app.route("/api/store-profile", methods=["POST"])
@jwt_required()
def store_profile():
    user_email = get_jwt_identity()
    data = request.json
    
    required_fields = ["name", "age", "gender", "height", "weight"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        age = int(data["age"])
        height = float(data["height"])
        weight = float(data["weight"])
        
        if age <= 0 or height <= 0 or weight <= 0:
            raise ValueError("Values must be positive")
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400

    bmi = calculate_bmi(weight, height)
    daily_calories = calculate_base_calories(weight, data.get("gender", "male"))

    profile_data = {
        "email": user_email,
        "name": data["name"],
        "age": age,
        "gender": data["gender"],
        "height": height,
        "weight": weight,
        "bmi": bmi,
        "daily_calories": daily_calories,
        "goals": data.get("goals", "maintain"),
        "updated_at": datetime.utcnow(),
    }
    result = profiles_collection.update_one(
        {"email": user_email},
        {"$set": profile_data},
        upsert=True
    )
    
    return jsonify({
        "message": "Profile stored successfully",
        "bmi": bmi,
        "daily_calories": daily_calories
    }), 201

def calculate_base_calories(weight_kg, gender="male"):
    """Simplified calorie calculation without activity level"""
    if gender.lower() == "female":
        return weight_kg * 22 * 0.9 
    return weight_kg * 22  

@app.route("/api/edit-profile", methods=["PUT"])
@jwt_required()
def edit_profile():
    user_email = get_jwt_identity()
    data = request.json
    
    name = data.get("name")
    age = data.get("age")
    gender = data.get("gender")
    height = data.get("height")
    weight = data.get("weight")

    if not any([name, age, gender, height, weight]):
        return jsonify({"error": "No fields to update"}), 400
    
    try:
        if age:
            age = int(age)
        if height:
            height = float(height)
        if weight:
            weight = float(weight)
    except ValueError:
        return jsonify({"error": "Invalid data format"}), 400

    update_data = {}
    if name:
        update_data["name"] = name
    if age:
        update_data["age"] = age
    if gender:
        update_data["gender"] = gender
    if height:
        update_data["height"] = height
    if weight:
        update_data["weight"] = weight

    if weight and height:
        update_data["bmi"] = calculate_bmi(weight, height)

    profiles_collection.update_one({"email": user_email}, {"$set": update_data})

    return jsonify({"message": "Profile updated successfully"}), 200

@app.route("/api/get-profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_email = get_jwt_identity()
    profile = profiles_collection.find_one({"email": user_email}, {"_id": 0})
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    return jsonify(profile), 200

@app.route("/api/get-bmi", methods=["GET"])
@jwt_required()
def get_bmi():
    user_email = get_jwt_identity()

    user = profiles_collection.find_one({"email": user_email}, {"_id": 0, "bmi": 1})

    if not user or "bmi" not in user:
        return jsonify({"error": "BMI not found. Please update your profile."}), 400

    return jsonify({"bmi": user["bmi"]}), 200

@app.route("/api/register",methods=["POST"])
def register():
    data=request.json
    email=data.get("email")
    password=data.get("password")

    if users_collection.find_one({"email":email}):
        return jsonify({"error":"User already exists"}),400

    hashed_password=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
    users_collection.insert_one({"email":email,"password":hashed_password})
    
    return jsonify({"message":"User registered successfully!"}),201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    stored_password = user["password"]
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')

    try:
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
            return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        try:
            if not bcrypt.check_password_hash(stored_password, password.encode('utf-8')):
                return jsonify({"error": "Invalid email or password"}), 401
        except Exception as e:
            return jsonify({"error": "Authentication error"}), 500

    profile = profiles_collection.find_one({"email": email})
    profile_complete = (
        profile
        and profile.get("name")
        and profile.get("age")
        and profile.get("gender")
        and profile.get("height")
        and profile.get("weight")
    )

    token = create_access_token(identity=email)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "profileComplete": profile_complete
    }), 200

otp_store = {}

def get_current_date():
    return datetime.utcnow().strftime("%Y-%m-%d")

@app.route("/api/update-steps", methods=["POST"])
@jwt_required()
def update_steps():
    data = request.json
    user_email = get_jwt_identity()
    new_steps = data.get("steps")
    current_date = datetime.utcnow().strftime("%Y-%m-%d")  

    if new_steps is None:
        return jsonify({"error": "Steps value is required"}), 400

    if "steps" not in db.list_collection_names():
        db.create_collection("steps")

    last_entry = steps_collection.find_one({"email": user_email, "date": current_date})

    if not last_entry:
        steps_collection.insert_one({
            "email": user_email,
            "date": current_date,
            "steps": new_steps,
            "last_updated": datetime.utcnow()
        })
    else:
        steps_collection.update_one(
            {"email": user_email, "date": current_date},
            {"$set": {"steps": new_steps, "last_updated": datetime.utcnow()}},
            upsert=True
        )

    return jsonify({"message": "Steps updated successfully!", "date": current_date}), 200



@app.route("/api/get-steps", methods=["GET"])
@jwt_required()
def get_steps():
    user_email = get_jwt_identity()
    current_date = get_current_date()

    today_steps = steps_collection.find_one(
        {"email": user_email, "date": current_date}, {"_id": 0, "steps": 1}
    )

    return jsonify({"steps": today_steps["steps"] if today_steps else 0, "date": current_date})

from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from datetime import datetime, timedelta

@app.route("/api/get-step-history", methods=["GET"])
@jwt_required()
def get_step_history():
    user_email = get_jwt_identity()
    today = datetime.utcnow().date()

    try:
        today_steps = steps_collection.find_one(
            {"email": user_email, "date": str(today)}, {"_id": 0, "steps": 1}
        )

        week_start = today - timedelta(days=6)  
        weekly_steps = steps_collection.aggregate([
            {"$match": {"email": user_email, "date": {"$gte": str(week_start), "$lte": str(today)}}},
            {"$group": {"_id": None, "total": {"$sum": "$steps"}}}
        ])
        weekly_steps = next(weekly_steps, {}).get("total", 0)

        month_start = today - timedelta(days=29)
        monthly_steps = steps_collection.aggregate([
            {"$match": {"email": user_email, "date": {"$gte": str(month_start), "$lte": str(today)}}},
            {"$group": {"_id": None, "total": {"$sum": "$steps"}}}
        ])
        monthly_steps = next(monthly_steps, {}).get("total", 0)

        return jsonify({
            "daily": today_steps["steps"] if today_steps else 0,
            "weekly": weekly_steps,
            "monthly": monthly_steps
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sleep-streak", methods=["GET"])
@jwt_required()
def get_sleep_streak():
    user_email = get_jwt_identity()
    
    try:
        sleep_data = list(sleep_collection.find(
            {"user": user_email},
            {"_id": 0, "date": 1}
        ).sort("date", -1))

        streak = 0
        previous_date = None

        for entry in sleep_data:
            current_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            
            if previous_date is None:
                streak += 1
            else:
                if (previous_date - current_date).days == 1:
                    streak += 1
                else:
                    break
            
            previous_date = current_date

        return jsonify({"streak": streak}), 200
    except Exception as e:
        print(f"Error calculating sleep streak: {e}")
        return jsonify({"error": "Failed to calculate sleep streak"}), 500

@app.route("/api/reset-sleep", methods=["POST"])
@jwt_required()
def reset_sleep():
    user_email = get_jwt_identity()
    
    user_challenges_collection.update_one(
        {"email": user_email, "challenge_name": "Sleep Tracker"},
        {"$set": {"progress": 0}}
    )
    
    return jsonify({"message": "Sleep value reset successfully!"}), 200
    
@app.route("/api/log-sleep", methods=["POST"])
@jwt_required()
def log_sleep():
    data = request.json
    user_email = get_jwt_identity()

    sleep_hours = float(data.get("sleep_hours", 0))
    sleep_rating = int(data.get("sleep_rating", 0))  
    date = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

    if sleep_hours <= 0:
        return jsonify({"error": "Invalid sleep hours"}), 400

    sleep_entry = {
        "user": user_email,
        "date": date,
        "sleep_hours": sleep_hours,
        "sleep_rating": sleep_rating,  
    }

    try:
        sleep_collection.insert_one(sleep_entry)

        
        achievement = None
        if sleep_hours >= 7:
            achievement = "🌙 Well-Rested Badge"
            achievements_collection.insert_one({
                "user": user_email,
                "title": "🎖 Well-Rested Badge",
                "description": "Congratulations! You've earned the Well-Rested Badge for sleeping more than 7 hours!",
                "likes": 0,
                "comments": []
            })

        return jsonify({
            "message": "Sleep data logged successfully!",
            "achievement": achievement
        }), 201
    except Exception as e:
        print(f"Error logging sleep: {e}")
        return jsonify({"error": "Failed to log sleep data"}), 500

def calculate_sleep_quality(sleep_history):
    if not sleep_history or len(sleep_history) < 3:
        return 0

    recent_sleep = sleep_history[:3]
    avg_sleep = sum(float(entry["sleep_hours"]) for entry in recent_sleep) / 3

    if avg_sleep >= 7:
        return 85  
    elif avg_sleep >= 6:
        return 70  
    else:
        return 55
      
@app.route("/api/sleep-history", methods=["GET"])
@jwt_required()
def get_sleep_history():
    user_email = get_jwt_identity()
    
    try:
        sleep_data = list(sleep_collection.find(
            {"user": user_email},
            {"_id": 0, "date": 1, "sleep_hours": 1}
        ).sort("date", -1).limit(7))

        sleep_quality = calculate_sleep_quality(sleep_data)
        sleep_distribution = calculate_sleep_distribution(sleep_data)

        return jsonify({
            "history": sleep_data,
            "sleep_quality": sleep_quality,
            "sleep_distribution": sleep_distribution
        }), 200
    except Exception as e:
        print(f"Error fetching sleep history: {e}")
        return jsonify({"error": "Failed to fetch sleep history"}), 500


@app.route("/api/get-achievements",methods=["GET"])
@jwt_required()
def get_achievements():
    user_email=get_jwt_identity()
    achievements=list(achievements_collection.find({"user": user_email},{"_id":0}))
    return jsonify(achievements)

def calculate_sleep_distribution(sleep_history):
    distribution = {
        "<6h": 0,
        "6-7h": 0,
        "7-8h": 0,
        ">8h": 0,
    }

    for entry in sleep_history:
        hours = float(entry["sleep_hours"])
        if hours < 6:
            distribution["<6h"] += 1
        elif hours < 7:
            distribution["6-7h"] += 1
        elif hours < 8:
            distribution["7-8h"] += 1
        else:
            distribution[">8h"] += 1

    return distribution

@app.route("/api/like-achievement",methods=["POST"])
@jwt_required()
def like_achievement():
    data=request.json
    user_email=get_jwt_identity()
    achievement_title=data.get("title")

    result = achievements_collection.update_one(
        {"title":achievement_title,"user":user_email},
        {"$inc":{"likes":1}}
    )

    if result.modified_count > 0:
        return jsonify({"message":"Achievement liked!"}),200
    return jsonify({"error": "Achievement not found"}),404



@app.route("/api/join-group", methods=["POST"])
@jwt_required()
def join_group():
    data = request.json
    user_email = get_jwt_identity()
    group_name = data.get("group_name")

    if not group_name:
        return jsonify({"error": "Group name is required"}), 400

    group = groups_collection.find_one({"name": group_name})

    if not group:
        return jsonify({"error": "Group does not exist. Use /api/create-group to create a new group."}), 404

    if user_email not in group.get("members", []):
        groups_collection.update_one({"name": group_name}, {"$addToSet": {"members": user_email}})
        return jsonify({"message": f"Joined {group_name} successfully!"}), 200

    return jsonify({"message": f"Already a member of {group_name}!"}), 200

@app.route("/api/create-group", methods=["POST"])
@jwt_required()
def create_group():
    data = request.json
    user_email = get_jwt_identity()
    group_name = data.get("group_name")

    if not group_name:
        return jsonify({"error": "Group name is required"}), 400

    existing_group = groups_collection.find_one({"name": group_name})
    if existing_group:
        return jsonify({"error": "Group already exists"}), 400

    new_group = {
        "name": group_name,
        "members": [user_email], 
        "posts": [],
        "created_at": datetime.utcnow().isoformat(),
    }

    groups_collection.insert_one(new_group)

    return jsonify({"message": f"Group '{group_name}' created successfully!"}), 201

@app.route("/api/get-group-details/<group_name>", methods=["GET"])
@jwt_required()
def get_group_details(group_name):
    user_email = get_jwt_identity()

    group = groups_collection.find_one({"name": group_name}, {"_id": 0})

    if not group:
        return jsonify({"error": "Group not found"}), 404

    if user_email not in group.get("members", []):
        return jsonify({"error": "You are not a member of this group"}), 403

    return jsonify(group), 200

@app.route("/api/delete-group", methods=["POST"])
@jwt_required()
def delete_group():
    data = request.json
    user_email = get_jwt_identity()
    group_name = data.get("group_name")

    if not group_name:
        return jsonify({"error": "Group name is required"}), 400

    group = groups_collection.find_one({"name": group_name})

    if not group:
        return jsonify({"error": "Group not found"}), 404

    if group.get("members", [])[0] != user_email:
        return jsonify({"error": "Only the group creator can delete this group"}), 403

    groups_collection.delete_one({"name": group_name})

    return jsonify({"message": f"Group '{group_name}' deleted successfully!"}), 200

@app.route("/api/leave-group", methods=["POST"])
@jwt_required()
def leave_group():
    try:
        data = request.json
        user = get_jwt_identity()
        group_name = data.get("group_name")

        if not group_name:
            return jsonify({"error": "Group name is required"}), 400

        group = groups_collection.find_one({"name": group_name})

        if not group:
            return jsonify({"error": "Group not found"}), 404

        if user not in group.get("members", []):
            return jsonify({"error": "You are not a member of this group"}), 403

        groups_collection.update_one(
            {"name": group_name},
            {"$pull": {"members": user}}
        )

        return jsonify({"message": f"Successfully left {group_name}"}), 200
    
    except Exception as e:
        print(f"Error in /api/leave-group: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/api/group-post", methods=["POST"])
@jwt_required()
def group_post():
    data = request.json
    user = get_jwt_identity()
    group_name = data.get("group_name")
    content = data.get("content")

    if not group_name or not content:
        return jsonify({"error": "Group name and content are required"}), 400

    group = groups_collection.find_one({"name": group_name})

    if not group or user not in group.get("members", []):
        return jsonify({"error": "You are not a member of this group"}), 403

    post = {
        "user": user,
        "content": content,
        "likes": 0,
        "comments": [],
        "timestamp": datetime.utcnow().isoformat(),
    }

    result = groups_collection.update_one({"name": group_name}, {"$push": {"posts": post}})

    if result.modified_count > 0:
        return jsonify({"message": "Post added successfully!", "redirect": True}), 201
    return jsonify({"error": "Group not found"}), 404

@app.route("/api/like-post", methods=["POST"])
@jwt_required()
def like_post():
    data = request.json
    user_email = get_jwt_identity()
    group_name = data.get("group_name")
    post_content = data.get("post_content")

    group = groups_collection.find_one({"name": group_name, "posts.content": post_content}, {"posts.$": 1})

    if not group or "posts" not in group or not group["posts"]:
        return jsonify({"error": "Post not found"}), 404

    post = group["posts"][0]
    post_owner = post["user"]

    if user_email in post.get("liked_by", []):
        return jsonify({"error": "You have already liked this post."}), 400

    result = groups_collection.update_one(
        {"name": group_name, "posts.content": post_content},
        {"$inc": {"posts.$.likes": 1}, "$push": {"posts.$.liked_by": user_email}}
    )

    if result.modified_count > 0:
        notifications_collection.insert_one({
            "user": post_owner,
            "message": f"{user_email} liked your post!",
            "timestamp": datetime.utcnow().isoformat(),
            "seen": False
        })
        return jsonify({"message": "Post liked successfully!"}), 200

    return jsonify({"error": "Failed to like post"}), 500

@app.route("/api/comment-post", methods=["POST"])
@jwt_required()
def comment_post():
    data = request.json
    user_email = get_jwt_identity()
    group_name = data.get("group_name")
    post_content = data.get("post_content")
    comment_text = data.get("comment")

    group = groups_collection.find_one({"name": group_name, "posts.content": post_content}, {"posts.$": 1})

    if not group or "posts" not in group or not group["posts"]:
        return jsonify({"error": "Post not found"}), 404

    post = group["posts"][0]
    post_owner = post["user"]

    result = groups_collection.update_one(
        {"name": group_name, "posts.content": post_content},
        {"$push": {"posts.$.comments": {"user": user_email, "text": comment_text}}}
    )

    if result.modified_count > 0:
        notifications_collection.insert_one({
            "user": post_owner,
            "message": f"{user_email} commented on your post: {comment_text}",
            "timestamp": datetime.utcnow().isoformat(),
            "seen": False
        })
        return jsonify({"message": "Comment added successfully!"}), 200

    return jsonify({"error": "Failed to add comment"}), 500

@app.route("/api/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user_email = get_jwt_identity()
    notifications = list(notifications_collection.find({"user": user_email}, {"_id": 0}))
    return jsonify(notifications), 200


@app.route("/api/get-group-posts/<group_name>", methods=["GET"])
@jwt_required()
def get_group_posts(group_name):
    user = get_jwt_identity()
    group = groups_collection.find_one({"name": group_name}, {"_id": 0, "members": 1, "posts": 1})

    if not group:
        return jsonify({"error": "Group not found"}), 404

    if user not in group["members"]:
        return jsonify({"error": "You are not a member of this group"}), 403

    return jsonify(group["posts"])


@app.route("/api/get-groups", methods=["GET"])
def get_groups():
    groups = list(groups_collection.find({}, {"_id": 0, "name": 1}))
    return jsonify(groups)

@app.route("/api/get-user-groups", methods=["GET"])
@jwt_required()
def get_user_groups():
    user_email = get_jwt_identity()

    user_groups = list(groups_collection.find({"members": user_email}, {"_id": 0, "name": 1}))

    group_names = [group["name"] for group in user_groups]

    return jsonify({"groups": group_names})

@app.route("/api/dislike-post", methods=["POST"])
@jwt_required()
def dislike_post():
    data = request.json
    group_name = data.get("group_name")
    post_content = data.get("post_content")

    result = groups_collection.update_one(
        {"name": group_name, "posts.content": post_content},
        {"$inc": {"posts.$.likes": -1}}
    )

    if result.modified_count > 0:
        return jsonify({"message": "Post disliked successfully!"}), 200
    return jsonify({"error": "Post not found"}), 404

@app.route("/api/remove-comment", methods=["POST"])
@jwt_required()
def remove_comment():
    data = request.json
    group_name = data.get("group_name")
    post_content = data.get("post_content")
    comment_text = data.get("comment")

    result = groups_collection.update_one(
        {"name": group_name, "posts.content": post_content},
        {"$pull": {"posts.$.comments": {"text": comment_text}}}
    )

    if result.modified_count > 0:
        return jsonify({"message": "Comment removed successfully!"}), 200
    return jsonify({"error": "Comment not found"}), 404

logging.basicConfig(level=logging.DEBUG)

from datetime import datetime

@app.route("/api/log-meal", methods=["POST"])
@jwt_required()
def log_meal():
    data = request.json
    user_email = get_jwt_identity()

    if not data or "meals" not in data:
        return jsonify({"error": "Invalid request, 'meals' field is required"}), 400

    meals = data.get("meals")

   
    global food_database
    if not isinstance(food_database, dict) or not food_database:
        return jsonify({"error": "Food database not loaded properly"}), 500

   
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fats = 0

    
    for meal_type, food_items in meals.items():
        if not isinstance(food_items, list): 
            food_items = [food_items] 
        
        for food_item in food_items:
            if food_item in food_database:
                food_info = food_database[food_item]
                total_calories += food_info.get("Calories (kcal)", 0)
                total_protein += food_info.get("Protein (g)", 0)
                total_carbs += food_info.get("Carbohydrates (g)", 0)
                total_fats += food_info.get("Fats (g)", 0)
            else:
                print(f"⚠ Warning: '{food_item}' not found in database!")

    meal_entry = {
        "user": user_email,
        "meals": meals, 
        "nutrition": {
            "calories": total_calories,
            "protein": total_protein,
            "carbs": total_carbs,
            "fats": total_fats,
        },
        "date": datetime.utcnow().isoformat()  
    }

    meal_collection.insert_one(meal_entry)

    return jsonify({
        "message": "Meal logged successfully!",
        "total_nutrition": meal_entry["nutrition"],
        "date": meal_entry["date"]
    }), 201

@app.route("/api/get-meals", methods=["GET"])
@jwt_required()
def get_meals():
    user_email = get_jwt_identity()

    try:
       
        print(f"🔍 Fetching meals for: {user_email}")

        meals = list(meal_collection.find({"user": user_email}, {"_id": 0})) 
        
        print(f"✅ Retrieved Meals: {meals}")

        if not meals:
            return jsonify({"meals": [], "message": "No meals found"}), 200 
        total_nutrition = {
            "calories": sum(meal.get("nutrition", {}).get("calories", 0) for meal in meals),
            "protein": sum(meal.get("nutrition", {}).get("protein", 0) for meal in meals),
            "carbs": sum(meal.get("nutrition", {}).get("carbs", 0) for meal in meals),
            "fats": sum(meal.get("nutrition", {}).get("fats", 0) for meal in meals),
        }

        return jsonify({"meals": meals, "overall_nutrition": total_nutrition}), 200

    except Exception as e:
        print(f"⚠ Error fetching meals: {e}")  
        return jsonify({"error": "Failed to load meals", "details": str(e)}), 500

@app.route("/api/get-food-items", methods=["GET"])
def get_food_items():
    return jsonify({"food_items": list(food_database.keys())})

@app.route("/api/track-progress", methods=["POST"])
@jwt_required()
def track_progress():
    user_email = get_jwt_identity()

    progress = progress_collection.find_one({"user": user_email}) or {"completed_days": 0}
    completed_days = progress["completed_days"] + 1 
    achievement_days = completed_days

    badge = None
    if completed_days == 3:
        badge = "🏅 Beginner Badge"
    elif completed_days == 5:
        badge = "🥈 Intermediate Badge"
    elif completed_days == 7:
        badge = "🏆 Advanced Badge"
        completed_days = 0  

    progress_collection.update_one(
        {"user": user_email},
        {"$set": {"completed_days": completed_days, "badge": badge}},
        upsert=True
    )

    if badge:
        achievements_collection.insert_one({
            "user": user_email,
            "title": f"🎖 {badge}",
            "description": f"Congratulations! You've earned the {badge} for completing {achievement_days} workout days!",
            "likes": 0,
            "comments": []
        })

    return jsonify({
        "message": "Workout day recorded!",
        "completed_days": completed_days,
        "badge": badge,
        "redirect": completed_days == 0  
    }), 200

@app.route("/api/get-progress", methods=["GET"])
@jwt_required()
def get_progress():
    user_email = get_jwt_identity()
    progress = progress_collection.find_one({"user": user_email}, {"_id": 0}) or {"completed_days": 0, "badge": None}
    return jsonify(progress)


@app.route("/api/reset-progress", methods=["POST"])
@jwt_required()
def reset_progress():
    user_email = get_jwt_identity()

    progress_collection.update_one(
        {"user": user_email},
        {"$set": {"completed_days": 0, "badge": None}}, 
        upsert=True
    )

    return jsonify({"message": "Progress reset successfully!"}), 200


@app.route("/api/post-badge", methods=["POST"])
@jwt_required()
def post_badge():
    try:
        data = request.json
        user_email = get_jwt_identity()
        
        group_name = data.get("group_name")
        badge = data.get("badge")

        if not group_name or not badge:
            return jsonify({"error": "Group name and badge are required!"}), 400

        group = groups_collection.find_one({"name": group_name})
        if not group:
            return jsonify({"error": "Group not found!"}), 404

        post = {
            "user": user_email,
            "content": f"🎉 Earned a new badge: {badge}!",
            "likes": 0,
            "comments": []
        }

        result = groups_collection.update_one({"name": group_name}, {"$push": {"posts": post}})

        if result.modified_count > 0:
            return jsonify({"message": "Badge posted successfully to the group!"}), 201
        return jsonify({"error": "Failed to post badge!"}), 500

    except Exception as e:
        print(f"⚠ Error in /api/post-badge: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500
@app.route("/test-read-excel", methods=["GET"])
def test_read_excel():
    try:
        file_path = os.path.join(os.getcwd(), "food_database.xlsx") 
        df = pd.read_excel(file_path) 
        return jsonify({
            "status": "success",
            "columns": df.columns.tolist(),
            "sample_data": df.head(5).to_dict(orient="records")
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000)) 
    app.run(host="0.0.0.0", port=port, debug=True)

