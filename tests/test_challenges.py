def test_join_challenge(client, auth_headers, app):
    """Test joining a challenge with various scenarios"""
    # Setup test challenge
    challenge_data = {
        "name": "10k Steps",
        "target": 10000,
        "description": "Walk 10,000 steps daily",
        "start_date": "2023-01-01",
        "end_date": "2023-01-31"
    }
    app.challenges_collection.insert_one(challenge_data)

    # Test successful challenge join
    response = client.post(
        '/api/challenges/join',
        json={"challenge_name": "10k Steps"},
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json['message'] == "Successfully joined challenge"
    assert "challenge_id" in response.json

    # Verify the join was recorded in database
    user_challenge = app.user_challenges_collection.find_one({
        "email": "test@example.com",  # From your auth fixture
        "challenge_name": "10k Steps"
    })
    assert user_challenge is not None
    assert user_challenge['progress'] == 0  # Initial progress should be 0

    # Test joining non-existent challenge
    invalid_response = client.post(
        '/api/challenges/join',
        json={"challenge_name": "Non-existent Challenge"},
        headers=auth_headers
    )
    assert invalid_response.status_code == 404
    assert "not found" in invalid_response.json['error'].lower()

    # Test duplicate challenge join
    duplicate_response = client.post(
        '/api/challenges/join',
        json={"challenge_name": "10k Steps"},
        headers=auth_headers
    )
    assert duplicate_response.status_code == 409
    assert "already joined" in duplicate_response.json['error'].lower()


def test_get_leaderboard(client, auth_headers, app):
    """Test leaderboard retrieval with various data scenarios"""
    # Setup test data
    challenge_name = "10k Steps"
    test_users = [
        {"email": "user1@example.com", "progress": 8500, "rank": 1},
        {"email": "user2@example.com", "progress": 7500, "rank": 2},
        {"email": "user3@example.com", "progress": 5000, "rank": 3},
    ]
    
    for user in test_users:
        app.user_challenges_collection.insert_one({
            "email": user["email"],
            "challenge_name": challenge_name,
            "progress": user["progress"]
        })

    # Test leaderboard retrieval
    response = client.get(
        f'/api/challenges/{challenge_name}/leaderboard',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    leaderboard = response.json['leaderboard']
    
    # Verify leaderboard structure and sorting
    assert len(leaderboard) == 3
    assert leaderboard[0]['email'] == "user1@example.com"
    assert leaderboard[0]['progress'] == 8500
    assert leaderboard[0]['rank'] == 1
    
    # Test leaderboard for non-existent challenge
    invalid_response = client.get(
        '/api/challenges/non-existent/leaderboard',
        headers=auth_headers
    )
    assert invalid_response.status_code == 404
    assert "not found" in invalid_response.json['error'].lower()

    # Test empty leaderboard case
    app.user_challenges_collection.delete_many({})
    empty_response = client.get(
        f'/api/challenges/{challenge_name}/leaderboard',
        headers=auth_headers
    )
    assert empty_response.status_code == 200
    assert len(empty_response.json['leaderboard']) == 0