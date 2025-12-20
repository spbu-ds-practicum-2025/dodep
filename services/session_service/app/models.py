from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    creator_id = Column(String)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    current_movie_id = Column(Integer, default=None)
    match_movie_id = Column(Integer, default=None)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    users = relationship("SessionUser", back_populates="session", cascade="all, delete-orphan")


class SessionUser(Base):
    __tablename__ = "session_users"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    user_id = Column(String, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    has_voted = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    session = relationship("Session", back_populates="users")
