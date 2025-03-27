def test_log_meal(client, auth_headers, mock_food_data, monkeypatch):
    monkeypatch.setattr('app.food_database', mock_food_data)
    response = client.post('/api/log-meal', json={
        "meals": {"breakfast": ["Apple"], "lunch": ["Chicken"]}
    }, headers=auth_headers)
    assert "total_nutrition" in response.json

def test_get_meal_plan(client, auth_headers, app):
    app.profiles_collection.insert_one({
        "email": "test@example.com",
        "bmi": 22,
        "daily_calories": 2000
    })
    response = client.get('/api/meal-plan', headers=auth_headers)
    assert "foods" in response.json