from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.database import Base
from app import models
import pytest
import os
import time

# Use PostgreSQL for testing
# Ensure this matches docker-compose.yml
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://user:password@localhost:5432/recommendation_db"
)

def get_test_engine(url):
    retries = 5
    while retries > 0:
        try:
            engine = create_engine(url)
            with engine.connect() as connection:
                pass
            return engine
        except Exception as e:
            print(f"Test DB connection failed: {e}. Retrying...")
            retries -= 1
            time.sleep(2)
    raise Exception("Could not connect to the test database")

engine = get_test_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Populate test data
@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    # Clear existing data
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    # Note: id is auto-increment in Postgres usually, but we can force it if needed or let it be generated.
    # For tests, it's better to let it be generated or be careful.
    # However, the original test hardcoded IDs.
    # Postgres sequences might get out of sync if we force IDs, but for a fresh test run it's fine.
    
    movies = [
        models.Movie(title="Movie 1", genre="Action", duration_minutes=120, rating=8.0, is_available=True),
        models.Movie(title="Movie 2", genre="Comedy", duration_minutes=90, rating=7.5, is_available=True),
        models.Movie(title="Movie 3", genre="Drama", duration_minutes=100, rating=8.5, is_available=True),
    ]
    db.add_all(movies)
    db.commit()
    
    db.close()
    yield
    # Cleanup
    Base.metadata.drop_all(bind=engine)

# Mock session check by setting env var
os.environ["SKIP_SESSION_CHECK"] = "true"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_movies():
    response = client.get("/movies?session=test_session")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["title"] == "Movie 1"

def test_get_next_movie():
    # Current movie is 1, next should be 2
    response = client.get("/recommendation/next?session=test_session&current_movie=1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["title"] == "Movie 2"

def test_get_next_movie_loop():
    # Current movie is 3 (last), next should be 1 (loop back)
    response = client.get("/recommendation/next?session=test_session&current_movie=3")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Movie 1"

def test_get_next_movie_invalid_current():
    # Current movie is 99 (doesn't exist), next should be 1 (first available)
    response = client.get("/recommendation/next?session=test_session&current_movie=99")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
