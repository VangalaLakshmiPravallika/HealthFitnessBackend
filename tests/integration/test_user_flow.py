import pytest

@pytest.mark.integration
def test_full_user_flow(client):
    # Register
    reg_res = client.post('/api/register',
                        json={"email": "test@example.com", "password": "test123"})
    assert reg_res.status_code == 201
    
    # Login
    login_res = client.post('/api/login',
                          json={"email": "test@example.com", "password": "test123"})
    token = login_res.json["token"]
    
    # Complete profile
    profile_data = {
        "name": "Test User",
        "age": 30,
        "gender": "male",
        "height": 175,
        "weight": 70
    }
    profile_res = client.post('/api/store-profile',
                            json=profile_data,
                            headers={"Authorization": f"Bearer {token}"})
    assert profile_res.status_code == 201
    
    # Get recommendations
    rec_res = client.get('/api/get-recommendations',
                        headers={"Authorization": f"Bearer {token}"})
    assert rec_res.status_code == 200