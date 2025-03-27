def test_log_sleep(client, auth_headers):
    response = client.post('/api/log-sleep', json={
        "sleep_hours": 7.5,
        "sleep_rating": 4
    }, headers=auth_headers)
    assert response.status_code == 201

def test_sleep_streak(client, auth_headers, app):
    app.sleep_collection.insert_many([
        {"user": "test@example.com", "date": "2023-01-01"},
        {"user": "test@example.com", "date": "2023-01-02"}
    ])
    response = client.get('/api/sleep-streak', headers=auth_headers)
    assert response.json['streak'] == 2