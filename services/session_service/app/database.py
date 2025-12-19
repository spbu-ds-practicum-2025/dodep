from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time

# PostgreSQL for production, SQLite for local development/testing
# According to tr.md, Session Service should use PostgreSQL
# In tests, will use in-memory SQLite automatically

# Default to SQLite for local development
# For production: set DATABASE_URL=postgresql://user:password@localhost/session_db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sessions.db")

def get_engine(url):
    # Retry logic for database connection (useful when waiting for DB to start)
    if "postgresql" in url:
        retries = 5
        while retries > 0:
            try:
                engine = create_engine(url)
                # Try to connect
                with engine.connect() as connection:
                    pass
                return engine
            except Exception as e:
                print(f"Database connection failed: {e}. Retrying in 2 seconds...")
                retries -= 1
                time.sleep(2)
        raise Exception("Could not connect to the database")
    else:
        return create_engine(
            url,
            connect_args={"check_same_thread": False}
        )

engine = get_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
