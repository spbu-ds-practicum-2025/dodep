"""
E2E tests for Session Service based on e2e-testing-plan.md
Tests for Part 1: Session Management Scenarios
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app, get_db
from app import models, database

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_sessions.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup test database and cleanup after each test"""
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


class TestSessionCreation:
    """Test 1.1.1: Successful session creation"""
    
    def test_create_session_success(self):
        """Test creating a new session"""
        response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "session_id" in data
        assert "session_code" in data
        assert "creator_id" in data
        assert "status" in data
        assert "current_movie_id" in data
        assert "participants" in data
        assert "created_at" in data
        
        # Validate response values
        assert data["creator_id"] == "user-001"
        assert data["status"] == "active"
        assert data["current_movie_id"] is None
        assert data["participants"] == ["user-001"]
        
        # Validate session code format (6 characters, alphanumeric)
        assert len(data["session_code"]) == 6
        assert data["session_code"].isalnum()
        
        # Validate session_id is integer
        assert isinstance(data["session_id"], int)
        assert data["session_id"] > 0
    
    def test_create_session_unique_codes(self):
        """Test that multiple sessions get unique codes"""
        response1 = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        response2 = client.post(
            "/sessions/create",
            json={"creator_id": "user-002"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        code1 = response1.json()["session_code"]
        code2 = response2.json()["session_code"]
        
        assert code1 != code2


class TestSessionJoin:
    """Test 1.1.2: Join existing session by code"""
    
    def test_join_session_success(self):
        """Test joining an existing session"""
        # Create session
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        
        # Join session
        join_response = client.post(
            "/sessions/join",
            json={"session_code": session_code, "user_id": "user-002"}
        )
        
        assert join_response.status_code == 200
        data = join_response.json()
        
        # Validate response structure
        assert "session_id" in data
        assert "session_code" in data
        assert "creator_id" in data
        assert "status" in data
        assert "participants" in data
        
        # Validate participants include both users
        assert "user-001" in data["participants"]
        assert "user-002" in data["participants"]
        assert len(data["participants"]) == 2
    
    def test_join_nonexistent_session(self):
        """Test joining a non-existent session"""
        response = client.post(
            "/sessions/join",
            json={"session_code": "INVALID", "user_id": "user-001"}
        )
        
        assert response.status_code == 404
    
    def test_join_completed_session(self):
        """Test joining a completed session"""
        # Create and complete session
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        
        # Complete session
        client.post(f"/sessions/{session_code}/complete")
        
        # Try to join
        join_response = client.post(
            "/sessions/join",
            json={"session_code": session_code, "user_id": "user-002"}
        )
        
        assert join_response.status_code == 400
    
    def test_rejoin_existing_user(self):
        """Test that existing user can rejoin (reactivate)"""
        # Create session
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        
        # Join with user-002
        client.post(
            "/sessions/join",
            json={"session_code": session_code, "user_id": "user-002"}
        )
        
        # Disconnect user-002
        client.post(f"/sessions/{session_code}/disconnect/user-002")
        
        # Rejoin with user-002
        rejoin_response = client.post(
            "/sessions/join",
            json={"session_code": session_code, "user_id": "user-002"}
        )
        
        assert rejoin_response.status_code == 200
        data = rejoin_response.json()
        assert "user-002" in data["participants"]


class TestSessionCompletion:
    """Test 1.1.3: Session completion"""
    
    def test_complete_session_success(self):
        """Test completing a session"""
        # Create session
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        
        # Complete session
        response = client.post(f"/sessions/{session_code}/complete")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response
        assert data["status"] == "completed"
        assert data["session_code"] == session_code
    
    def test_complete_nonexistent_session(self):
        """Test completing a non-existent session"""
        response = client.post("/sessions/INVALID/complete")
        assert response.status_code == 404
    
    def test_get_completed_session(self):
        """Test retrieving a completed session"""
        # Create and complete session
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        
        client.post(f"/sessions/{session_code}/complete")
        
        # Get session
        response = client.get(f"/sessions/{session_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"


class TestSessionRetrieval:
    """Test session retrieval endpoints"""
    
    def test_get_session_by_code(self):
        """Test retrieving session by code"""
        # Create session
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        session_id = create_response.json()["session_id"]
        
        # Get session
        response = client.get(f"/sessions/{session_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == session_id
        assert data["session_code"] == session_code
        assert data["creator_id"] == "user-001"
        assert data["status"] == "active"
    
    def test_validate_session(self):
        """Test session validation endpoint"""
        # Create session with multiple participants
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        session_id = create_response.json()["session_id"]
        
        # Add participant
        client.post(
            "/sessions/join",
            json={"session_code": session_code, "user_id": "user-002"}
        )
        
        # Validate session
        response = client.get(f"/sessions/{session_code}/validate")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is True
        assert data["session_id"] == session_id
        assert data["status"] == "active"
        assert "user-001" in data["participants"]
        assert "user-002" in data["participants"]


class TestMultipleParticipants:
    """Test scenarios with multiple participants"""
    
    def test_session_with_three_participants(self):
        """Test session with 3 participants"""
        # Create session
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        
        # Add second participant
        client.post(
            "/sessions/join",
            json={"session_code": session_code, "user_id": "user-002"}
        )
        
        # Add third participant
        join_response = client.post(
            "/sessions/join",
            json={"session_code": session_code, "user_id": "user-003"}
        )
        
        assert join_response.status_code == 200
        data = join_response.json()
        
        assert len(data["participants"]) == 3
        assert all(user in data["participants"] for user in ["user-001", "user-002", "user-003"])
    
    def test_disconnect_and_check_participants(self):
        """Test disconnecting user and checking participant list"""
        # Create session with 2 participants
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        
        client.post(
            "/sessions/join",
            json={"session_code": session_code, "user_id": "user-002"}
        )
        
        # Get initial participants
        response1 = client.get(f"/sessions/{session_code}")
        assert len(response1.json()["participants"]) == 2
        
        # Disconnect user-002
        client.post(f"/sessions/{session_code}/disconnect/user-002")
        
        # Check participants after disconnect
        response2 = client.get(f"/sessions/{session_code}")
        data = response2.json()
        
        assert len(data["participants"]) == 1
        assert data["participants"] == ["user-001"]


class TestUpdateCurrentMovie:
    """Test updating current movie in session"""
    
    def test_update_current_movie(self):
        """Test updating the current movie for a session"""
        # Create session
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        
        # Initially should be None
        assert create_response.json()["current_movie_id"] is None
        
        # Update current movie to movie_id = 1
        response = client.put(
            f"/sessions/{session_code}/movie",
            json={"current_movie_id": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_movie_id"] == 1
        
        # Verify by retrieving session
        get_response = client.get(f"/sessions/{session_code}")
        assert get_response.json()["current_movie_id"] == 1
    
    def test_update_current_movie_nonexistent_session(self):
        """Test updating movie in non-existent session"""
        response = client.put(
            "/sessions/INVALID/movie",
            json={"current_movie_id": 1}
        )
        assert response.status_code == 404
    
    def test_update_current_movie_multiple_times(self):
        """Test updating movie multiple times"""
        # Create session
        create_response = client.post(
            "/sessions/create",
            json={"creator_id": "user-001"}
        )
        session_code = create_response.json()["session_code"]
        
        # Update to movie 1
        client.put(f"/sessions/{session_code}/movie", json={"current_movie_id": 1})
        response1 = client.get(f"/sessions/{session_code}")
        assert response1.json()["current_movie_id"] == 1
        
        # Update to movie 2
        client.put(f"/sessions/{session_code}/movie", json={"current_movie_id": 2})
        response2 = client.get(f"/sessions/{session_code}")
        assert response2.json()["current_movie_id"] == 2
        
        # Update to movie 3
        client.put(f"/sessions/{session_code}/movie", json={"current_movie_id": 3})
        response3 = client.get(f"/sessions/{session_code}")
        assert response3.json()["current_movie_id"] == 3


class TestSessionHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
