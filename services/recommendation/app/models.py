from sqlalchemy import Column, Integer, String, Boolean, Float
from .database import Base

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    genre = Column(String)
    duration_minutes = Column(Integer)
    rating = Column(Float)
    description = Column(String)
    poster_url = Column(String)
    is_available = Column(Boolean, default=True)
