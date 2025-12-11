import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add app directory to sys.path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../app"))

from main import app
from models import SwipeRequest

client = TestClient(app)

@pytest.fixture
def mock_redis():
    with patch("service.get_redis_client") as mock:
        redis_instance = MagicMock()
        mock.return_value = redis_instance
        yield redis_instance

@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock_client:
        yield mock_client

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_swipe_want_now_incomplete(mock_redis):
    # Setup Redis mock
    # When hgetall is called, return only current user's vote
    mock_redis.hgetall.return_value = {"vote:user1": "want_now"}
    
    payload = {
        "session_id": "session123",
        "user_id": "user1",
        "movie_id": "movie456",
        "swipe_value": "want_now",
        "participants": ["user1", "user2"]
    }
    
    response = client.post("/swipe", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == "vote_recorded"
    assert data["user_id"] == "user1"
    assert data["completed"] == False
    
    # Verify Redis calls
    mock_redis.hset.assert_called()

@pytest.mark.asyncio
async def test_swipe_want_now_match(mock_redis):
    # Setup Redis mock to simulate all users voted want_now
    mock_redis.hgetall.return_value = {
        "vote:user1": "want_now",
        "vote:user2": "want_now"
    }
    
    payload = {
        "session_id": "session123",
        "user_id": "user2", # Second user voting
        "movie_id": "movie456",
        "swipe_value": "want_now",
        "participants": ["user1", "user2"]
    }
    
    response = client.post("/swipe", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == "match_found"
    assert data["payload"]["movie_id"] == "movie456"
    assert set(data["payload"]["participants"]) == {"user1", "user2"}

@pytest.mark.asyncio
async def test_swipe_skip(mock_redis):
    # Mock external service calls
    with patch("service.get_next_movie", new_callable=AsyncMock) as mock_get_next:
        with patch("service.update_session_movie", new_callable=AsyncMock) as mock_update:
            
            mock_get_next.return_value = "movie789"
            
            payload = {
                "session_id": "session123",
                "user_id": "user1",
                "movie_id": "movie456",
                "swipe_value": "skip",
                "participants": ["user1", "user2"]
            }
            
            response = client.post("/swipe", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["event"] == "next_movie"
            assert data["payload"]["movie_id"] == "movie789"
            assert data["payload"]["reason"] == "skip"
            
            # Verify interactions
            mock_redis.hset.assert_called() # Vote saved
            mock_redis.delete.assert_called() # Votes cleared
            mock_get_next.assert_called_with("session123", "movie456")
            mock_update.assert_called_with("session123", "movie789")

@pytest.mark.asyncio
async def test_swipe_skip_service_failure(mock_redis):
    # Test what happens if external service fails
    with patch("service.get_next_movie", new_callable=AsyncMock) as mock_get_next:
        mock_get_next.return_value = None # Simulate failure
        
        payload = {
            "session_id": "session123",
            "user_id": "user1",
            "movie_id": "movie456",
            "swipe_value": "skip",
            "participants": ["user1", "user2"]
        }
        
        response = client.post("/swipe", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["event"] == "error"
