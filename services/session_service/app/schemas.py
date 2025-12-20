from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SessionUserBase(BaseModel):
    user_id: str


class SessionUserCreate(SessionUserBase):
    pass


class VoteRequest(BaseModel):
    user_id: str
    movie_id: int


class SessionUser(SessionUserBase):
    id: int
    session_id: int
    joined_at: datetime
    is_active: bool
    has_voted: bool
    last_seen: datetime

    class Config:
        orm_mode = True


class SessionBase(BaseModel):
    creator_id: str


class SessionCreate(SessionBase):
    pass


class SessionJoin(BaseModel):
    session_code: str
    user_id: str


class Session(SessionBase):
    id: int
    code: str
    status: str
    current_movie_id: Optional[int] = None
    match_movie_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    users: List[SessionUser] = []

    class Config:
        orm_mode = True


class SessionResponse(BaseModel):
    session_id: int
    session_code: str
    creator_id: str
    status: str
    current_movie_id: Optional[int] = None
    match_movie_id: Optional[int] = None
    participants: List[str]
    created_at: datetime

    class Config:
        orm_mode = True


class ValidateSessionResponse(BaseModel):
    is_valid: bool
    session_id: int
    status: str
    participants: List[str]
    current_movie_id: Optional[int] = None

    class Config:
        orm_mode = True


class UpdateMovieRequest(BaseModel):
    current_movie_id: int


class UpdateMatchRequest(BaseModel):
    match_movie_id: int


class ContinueSessionRequest(BaseModel):
    next_movie_id: int
