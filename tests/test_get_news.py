import sys
import os
import pytest
import json
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app  

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

def test_get_news_success(client):
    mock_articles = [
        {
            "title": "Health Tips",
            "description": "Stay healthy by exercising daily.",
            "url": "https://example.com/health",
            "urlToImage": "https://example.com/image.jpg",
            "publishedAt": "2023-01-01T00:00:00Z"
        },
        {
            "title": "Fitness News",
            "description": "10 ways to stay fit.",
            "url": "https://example.com/fitness",
            "urlToImage": "https://example.com/image2.jpg",
            "publishedAt": "2023-01-02T00:00:00Z"
        }
    ]

    with patch("backend.app.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"articles": mock_articles}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get("/api/news")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert data[0]["title"] == "Health Tips"
        assert data[1]["url"] == "https://example.com/fitness"
import requests

@patch("backend.app.requests.get")
def test_get_news_api_failure(mock_get, client):
    mock_get.side_effect = requests.exceptions.RequestException("API request failed")

    response = client.get("/api/news")

    assert response.status_code == 500
    json_data = response.get_json()
    assert "error" in json_data
    assert json_data["error"] == "API request failed"

