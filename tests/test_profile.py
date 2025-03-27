def test_store_profile(client, auth_headers):
    response = client.post('/api/store-profile', json={
        "name": "Test User",
        "age": 30,
        "gender": "male",
        "height": 175,
        "weight": 70
    }, headers=auth_headers)
    assert response.status_code == 201
    assert "bmi" in response.json

def test_get_bmi(client, auth_headers, app):
    app.profiles_collection.insert_one({
        "email": "test@example.com",
        "bmi": 22.5
    })
    response = client.get('/api/get-bmi', headers=auth_headers)
    assert response.json['bmi'] == 22.5