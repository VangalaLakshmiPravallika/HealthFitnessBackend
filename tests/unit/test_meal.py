def test_log_meal(client, auth):
    token = auth.login()
    response = client.post('/api/log-meal',
                         json={"meals": {"breakfast": ["Oatmeal"]}},
                         headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert "total_nutrition" in response.json

def test_get_meals(client, auth):
    token = auth.login()
    client.post('/api/log-meal',
              json={"meals": {"breakfast": ["Oatmeal"]}},
              headers={"Authorization": f"Bearer {token}"})
    response = client.get('/api/get-meals',
                        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json["meals"]) > 0