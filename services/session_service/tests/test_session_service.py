import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, get_db
from app.database import Base

# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_create_session():
    """Test creating a new session"""
    response = client.post("/sessions/create", json={"creator_id": "user1"})
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "user1"
    assert data["session_code"] is not None
    assert data["status"] == "active"
    assert "user1" in data["participants"]
    assert data["current_movie_id"] is None


def test_join_session():
    """Test joining an existing session"""
    # Create session first
    create_response = client.post("/sessions/create", json={"creator_id": "user1"})
    session_code = create_response.json()["session_code"]
    
    # Join session
    join_response = client.post(
        "/sessions/join",
        json={"session_code": session_code, "user_id": "user2"}
    )
    assert join_response.status_code == 200
    data = join_response.json()
    assert "user1" in data["participants"]
    assert "user2" in data["participants"]


def test_join_nonexistent_session():
    """Test joining a non-existent session"""
    response = client.post(
        "/sessions/join",
        json={"session_code": "INVALID", "user_id": "user1"}
    )
    assert response.status_code == 404


def test_get_session():
    """Test getting session details"""
    # Create session
    create_response = client.post("/sessions/create", json={"creator_id": "user1"})
    session_code = create_response.json()["session_code"]
    
    # Get session
    response = client.get(f"/sessions/{session_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_code"] == session_code
    assert data["creator_id"] == "user1"


def test_validate_session():
    """Test validating session"""
    # Create session
    create_response = client.post("/sessions/create", json={"creator_id": "user1"})
    session_code = create_response.json()["session_code"]
    
    # Validate session
    response = client.get(f"/sessions/{session_code}/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert "user1" in data["participants"]


def test_update_current_movie():
    """Test updating current movie"""
    # Create session
    create_response = client.post("/sessions/create", json={"creator_id": "user1"})
    session_code = create_response.json()["session_code"]
    
    # Update movie
    response = client.put(
        f"/sessions/{session_code}/movie",
        json={"current_movie_id": 42}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_movie_id"] == 42


def test_disconnect_user():
    """Test disconnecting a user"""
    # Create and join session
    create_response = client.post("/sessions/create", json={"creator_id": "user1"})
    session_code = create_response.json()["session_code"]
    
    client.post(
        "/sessions/join",
        json={"session_code": session_code, "user_id": "user2"}
    )
    
    # Disconnect user
    response = client.post(f"/sessions/{session_code}/disconnect/user2")
    assert response.status_code == 200
    assert response.json()["status"] == "disconnected"


def test_complete_session():
    """Test completing a session"""
    # Create session
    create_response = client.post("/sessions/create", json={"creator_id": "user1"})
    session_code = create_response.json()["session_code"]
    
    # Complete session
    response = client.post(f"/sessions/{session_code}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
