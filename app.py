import os
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import logging
from datetime import datetime
from datetime import datetime, timedelta

load_dotenv()

app=Flask(__name__)
CORS(app)

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

app.config["JWT_SECRET_KEY"]=os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

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

@app.route("/api/get-challenges", methods=["GET"])
@jwt_required()
def get_challenges():
    challenges = list(challenges_collection.find({}, {"_id": 0}))
    return jsonify({"challenges": challenges}), 200

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
        return jsonify({"message": f"Congratulations! You completed '{challenge_name}' 🎉"}), 200

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
    leaderboard = list(user_challenges_collection.find({"challenge_name": challenge_name}, {"_id": 0, "email": 1, "progress": 1}))

    leaderboard_sorted = sorted(leaderboard, key=lambda x: x["progress"], reverse=True)
    
    return jsonify({"leaderboard": leaderboard_sorted}), 200


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
    
    name = data.get("name")
    age = data.get("age")
    gender = data.get("gender")
    height = data.get("height")
    weight = data.get("weight")

    if not all([name, age, gender, height, weight]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        age = int(age)
        height = float(height)
        weight = float(weight)
    except ValueError:
        return jsonify({"error": "Invalid data format"}), 400

    bmi = calculate_bmi(weight, height)

    profile_data = {
        "email": user_email,
        "name": name,
        "age": age,
        "gender": gender,
        "height": height,
        "weight": weight,
        "bmi": bmi,
        "created_at": datetime.utcnow(),
    }
    
    profiles_collection.update_one({"email": user_email}, {"$set": profile_data}, upsert=True)

    return jsonify({"message": "Profile stored successfully", "bmi": bmi}), 201

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

@app.route("/api/get-bmi", methods=["POST"])
@jwt_required()
def get_bmi():
    data = request.json
    height = data.get("height")
    weight = data.get("weight")

    if not height or not weight:
        return jsonify({"error": "Height and weight are required"}), 400
    
    try:
        height = float(height)
        weight = float(weight)
    except ValueError:
        return jsonify({"error": "Invalid input"}), 400

    bmi = calculate_bmi(weight, height)
    return jsonify({"bmi": bmi}), 200

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

    user = users_collection.find_one({"email": email})

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    stored_password = user["password"]
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')

    if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
        return jsonify({"error": "Invalid email or password"}), 401

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
    
    # Reset sleep value in the database
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

@app.route("/api/get-notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user_email = get_jwt_identity()

    notifications = list(
        db.notifications.find(
            {"user": user_email}, 
            {"_id": 0}  
        ).sort("timestamp", -1) 
    )

    db.notifications.update_many(
        {"user": user_email, "seen": False}, 
        {"$set": {"seen": True}}
    )

    return jsonify({"notifications": notifications}), 200



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
        db.notifications.insert_one({
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
        db.notifications.insert_one({
            "user": post_owner,
            "message": f"{user_email} commented on your post: {comment_text}",
            "timestamp": datetime.utcnow().isoformat(),
            "seen": False
        })
        return jsonify({"message": "Comment added successfully!"}), 200

    return jsonify({"error": "Failed to add comment"}), 500



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


@app.route("/api/get-fitness-level", methods=["GET"])
@jwt_required()
def get_fitness_level():
    user_email = get_jwt_identity()
    user_data = db.fitness_assessment.find_one({"user": user_email})

    if not user_data:
        return jsonify({"error": "No fitness level found. Please complete the assessment first."}), 400

    return jsonify({"fitness_level": user_data["level"]})

@app.route("/api/workout-plan", methods=["GET"])
@jwt_required()
def get_workout_plan():
    user_email = get_jwt_identity()
    user_data = db.fitness_assessment.find_one({"user": user_email})

    if not user_data:
        return jsonify({"error": "No fitness level found. Please complete the assessment first."}), 400

    fitness_level = user_data["level"]

    workout_plans = {
        "Beginner 🟢": [
            {"day": "Day 1", "workout": "Jumping Jacks x 30 sec, Squats x 10, Push-ups x 5"},
            {"day": "Day 2", "workout": "High Knees x 30 sec, Lunges x 10, Plank x 20 sec"},
            {"day": "Day 3", "workout": "Mountain Climbers x 30 sec, Wall Sit x 20 sec, Crunches x 15"},
            {"day": "Day 4", "workout": "Jogging in Place x 30 sec, Bridges x 10, Shoulder Taps x 10"},
            {"day": "Day 5", "workout": "Burpees x 5, Side Lunges x 10, Plank x 30 sec"},
        ],
        "Intermediate 🟡": [
            {"day": "Day 1", "workout": "Jump Rope x 1 min, Squats x 20, Push-ups x 10"},
            {"day": "Day 2", "workout": "Burpees x 10, Lunges x 15, Plank x 40 sec"},
            {"day": "Day 3", "workout": "Mountain Climbers x 30 sec, Bicycle Crunches x 20, Wall Sit x 30 sec"},
            {"day": "Day 4", "workout": "Jogging x 3 min, Box Jumps x 10, Plank Shoulder Taps x 15"},
            {"day": "Day 5", "workout": "Jump Squats x 15, Bulgarian Split Squats x 10, Plank x 1 min"},
        ],
        "Advanced 🔴": [
            {"day": "Day 1", "workout": "Sprint x 2 min, Push-ups x 30, Squats x 30"},
            {"day": "Day 2", "workout": "Burpees x 20, Pull-ups x 10, Hanging Leg Raises x 15"},
            {"day": "Day 3", "workout": "Box Jumps x 20, Dead Hangs x 30 sec, Dips x 15"},
            {"day": "Day 4", "workout": "Running x 5 min, Power Cleans x 10, Plank Hold x 2 min"},
            {"day": "Day 5", "workout": "Jump Lunges x 20, Front Squats x 15, Push Press x 12"},
        ],
    }

    return jsonify({"workout_plan": workout_plans.get(fitness_level, [])})
@app.route("/api/fitness-assessment", methods=["POST"])
@jwt_required()
def fitness_assessment():
    data = request.json
    user_email = get_jwt_identity()

    try:
        pushups = int(data.get("pushups", 0))
        squats = int(data.get("squats", 0))
        plank_seconds = int(data.get("plank_seconds", 0))

        if pushups < 10 or squats < 10 or plank_seconds < 20:
            level = "Beginner 🟢"
        elif pushups < 20 or squats < 20 or plank_seconds < 40:
            level = "Intermediate 🟡"
        else:
            level = "Advanced 🔴"

        db.fitness_assessment.update_one(
            {"user": user_email},
            {"$set": {"level": level, "data": data}},
            upsert=True
        )

        return jsonify({"message": "Assessment Completed!", "fitness_level": level}), 200

    except ValueError:
        return jsonify({"error": "Invalid input! Please enter numeric values."}), 400

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

