from pydantic import BaseModel
from typing import List, Optional, Literal

class SwipeRequest(BaseModel):
    session_id: str
    user_id: str
    movie_id: str
    swipe_value: Literal["want_now", "skip"]
    participants: List[str]  # List of user_ids in the session

class MatchPayload(BaseModel):
    movie_id: str
    participants: List[str]

class NextMoviePayload(BaseModel):
    movie_id: str
    reason: str

class SwipeResponse(BaseModel):
    event: Literal["match_found", "vote_recorded", "next_movie", "error"]
    payload: Optional[MatchPayload | NextMoviePayload | dict] = None
    user_id: Optional[str] = None
    completed: Optional[bool] = None
