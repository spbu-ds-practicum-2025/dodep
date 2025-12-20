from pydantic import BaseModel
from typing import List, Optional, Literal, Union

class SwipeRequest(BaseModel):
    session_id: Union[int, str]
    user_id: Union[int, str]
    movie_id: Union[int, str]
    swipe_value: Literal["want_now", "skip"]
    participants: List[Union[int, str]]

class MatchedMovie(BaseModel):
    id: Union[int, str]
    title: Optional[str] = None

class SwipeResponse(BaseModel):
    status: Literal["match_found", "vote_recorded", "next_movie", "error"]
    session_id: Optional[Union[int, str]] = None
    movie_id: Optional[Union[int, str]] = None
    votes_count: Optional[int] = None
    required_votes: Optional[int] = None
    matched_movie: Optional[MatchedMovie] = None
    message: Optional[str] = None


class CheckStatusRequest(BaseModel):
    session_id: Union[int, str]
    current_movie_id: Union[int, str]
    participants: List[Union[int, str]]
