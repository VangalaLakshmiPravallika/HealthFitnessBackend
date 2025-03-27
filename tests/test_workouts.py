import pandas as pd

def test_get_recommendations(client, auth_headers, monkeypatch):
    mock_exercises = pd.DataFrame([{
        "id": 1, "name": "Push-up", "bodyPart": "chest", "equipment": "body weight"
    }])
    
    monkeypatch.setattr('app.exercises_df', mock_exercises)
    response = client.get('/api/get-recommendations', headers=auth_headers)
    assert "recommended_workouts" in response.json