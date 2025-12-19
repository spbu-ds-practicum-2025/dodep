from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL for production, SQLite for local development/testing
# According to tr.md, Session Service should use PostgreSQL
# In tests, will use in-memory SQLite automatically

# Default to SQLite for local development
# For production: set DATABASE_URL=postgresql://user:password@localhost/session_db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sessions.db")

engine = create_engine(
    DATABASE_URL,
    # SQLite specific options (no-op for PostgreSQL)
    **({} if "postgresql" in DATABASE_URL else {"connect_args": {"check_same_thread": False}})
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
