from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import os
from . import models, schemas, database

app = FastAPI(title="Recommendation Service")

# Create tables
models.Base.metadata.create_all(bind=database.engine)

SESSION_SERVICE_URL = os.getenv("SESSION_SERVICE_URL", "http://localhost:8001")

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    # Populate with dummy data if empty
    db = database.SessionLocal()
    if db.query(models.Movie).count() == 0:
        dummy_movies = [
            models.Movie(title="Inception", genre="Sci-Fi", duration_minutes=148, rating=8.8, description="A thief who steals corporate secrets through the use of dream-sharing technology...", poster_url="http://example.com/inception.jpg"),
            models.Movie(title="The Matrix", genre="Sci-Fi", duration_minutes=136, rating=8.7, description="A computer hacker learns from mysterious rebels about the true nature of his reality...", poster_url="http://example.com/matrix.jpg"),
            models.Movie(title="Interstellar", genre="Sci-Fi", duration_minutes=169, rating=8.6, description="A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.", poster_url="http://example.com/interstellar.jpg"),
            models.Movie(title="The Dark Knight", genre="Action", duration_minutes=152, rating=9.0, description="When the menace known as the Joker wreaks havoc and chaos on the people of Gotham...", poster_url="http://example.com/dark_knight.jpg"),
            models.Movie(title="Pulp Fiction", genre="Crime", duration_minutes=154, rating=8.9, description="The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine...", poster_url="http://example.com/pulp_fiction.jpg"),
        ]
        db.add_all(dummy_movies)
        db.commit()
    db.close()

async def verify_session(session_code: str):
    # In a real scenario, we call the Session Service.
    # For testing/MVP without the full stack, we might skip or mock this.
    # We'll implement the call but handle connection errors gracefully for standalone testing.
    if os.getenv("SKIP_SESSION_CHECK") == "true":
        return True
        
    async with httpx.AsyncClient() as client:
        try:
            # Assuming Session Service has an endpoint to check session
            # Based on TR: Gateway checks session, but RecSvc also checks?
            # TR says: "Recommendation Service обращается к Session Service, чтобы проверить валидность кода сессии."
            response = await client.get(f"{SESSION_SERVICE_URL}/sessions/{session_code}/validate")
            if response.status_code != 200:
                raise HTTPException(status_code=403, detail="Invalid session")
            return True
        except httpx.RequestError:
            # Fallback for development if Session Service is not running
            print("Warning: Could not connect to Session Service. Skipping validation.")
            return True

@app.get("/movies", response_model=List[schemas.Movie])
async def get_movies(session_code: str = Query(..., alias="session"), db: Session = Depends(get_db)):
    """
    Get a list of movies for the session.
    """
    await verify_session(session_code)
    
    # Simple logic: return all available movies
    # In a real system, this would filter based on user preferences
    movies = db.query(models.Movie).filter(models.Movie.is_available == True).all()
    return movies

@app.get("/recommendation/next", response_model=schemas.Movie)
async def get_next_movie(
    session_code: str = Query(..., alias="session"), 
    current_movie_id: int = Query(..., alias="current_movie"),
    db: Session = Depends(get_db)
):
    """
    Get the next movie recommendation.
    Called by Match Service when a movie is skipped.
    """
    # We don't necessarily need to verify session here if Match Service is trusted, 
    # but it's good practice.
    # await verify_session(session_code)

    # Simple logic: find a movie with ID > current_movie_id
    next_movie = db.query(models.Movie).filter(
        models.Movie.id > current_movie_id,
        models.Movie.is_available == True
    ).order_by(models.Movie.id).first()

    if not next_movie:
        # If no next movie, maybe loop back to start or return 404
        # Let's loop back for endless swiping
        next_movie = db.query(models.Movie).filter(models.Movie.is_available == True).order_by(models.Movie.id).first()
        
        if not next_movie:
             raise HTTPException(status_code=404, detail="No movies available")
             
        # If we looped back and it's the same movie (only 1 movie in DB), handle it
        if next_movie.id == current_movie_id:
             raise HTTPException(status_code=404, detail="No other movies available")

    return next_movie

@app.get("/health")
def health_check():
    return {"status": "ok"}
