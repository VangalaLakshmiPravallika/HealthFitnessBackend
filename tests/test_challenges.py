def test_join_challenge(client, auth_headers, app):
    app.challenges_collection.insert_one({"name": "10k Steps", "target": 10000})
    response = client.post('/api/join-challenge', json={
        "challenge_name": "10k Steps"
    }, headers=auth_headers)
    assert response.status_code == 201

def test_get_leaderboard(client, auth_headers, app):
    app.user_challenges_collection.insert_one({
        "email": "user1@example.com",
        "challenge_name": "10k Steps",
        "progress": 5000
    })
    response = client.get('/api/get-leaderboard/10k Steps', headers=auth_headers)
    assert "leaderboard" in response.json