from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time

# Default to PostgreSQL, but allow override
# Format: postgresql://user:password@host:port/dbname
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost:5432/recommendation_db"
)

def get_engine(url):
    # Retry logic for database connection (useful when waiting for DB to start)
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

engine = get_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
