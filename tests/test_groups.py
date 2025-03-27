def test_create_group(client, auth_headers):
    response = client.post('/api/create-group', json={
        "group_name": "Fitness Warriors"
    }, headers=auth_headers)
    assert response.status_code == 201

def test_group_post(client, auth_headers, app):
    app.groups_collection.insert_one({
        "name": "Fitness Warriors",
        "members": ["test@example.com"]
    })
    response = client.post('/api/group-post', json={
        "group_name": "Fitness Warriors",
        "content": "Hello group!"
    }, headers=auth_headers)
    assert response.status_code == 201