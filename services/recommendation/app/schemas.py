from pydantic import BaseModel
from typing import Optional, List

class MovieBase(BaseModel):
    title: str
    genre: str
    duration_minutes: int
    rating: float
    description: Optional[str] = None
    poster_url: Optional[str] = None

class MovieCreate(MovieBase):
    pass

class Movie(MovieBase):
    id: int
    is_available: bool

    class Config:
        orm_mode = True

class NextMovieRequest(BaseModel):
    session_id: str
    current_movie_id: int
