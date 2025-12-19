from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import os
import string
import random
from datetime import datetime
from . import models, schemas, database

app = FastAPI(title="Session Service")

# Create tables
models.Base.metadata.create_all(bind=database.engine)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_session_code(length: int = 6) -> str:
    """Generate a unique session code"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


@app.get("/")
async def root():
    return {"message": "Session Service is running", "docs": "/docs"}


@app.post("/sessions/create", response_model=schemas.SessionResponse)
async def create_session(request: schemas.SessionCreate, db: Session = Depends(get_db)):
    """
    Create a new session
    """
    # Generate unique session code
    session_code = generate_session_code()
    while db.query(models.Session).filter(models.Session.code == session_code).first():
        session_code = generate_session_code()
    
    # Create session
    db_session = models.Session(
        code=session_code,
        creator_id=request.creator_id,
        status=models.SessionStatus.WAITING
    )
    db.add(db_session)
    db.flush()
    
    # Add creator as first participant
    db_user = models.SessionUser(
        session_id=db_session.id,
        user_id=request.creator_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_session)
    
    return schemas.SessionResponse(
        session_id=db_session.id,
        session_code=db_session.code,
        creator_id=db_session.creator_id,
        status=db_session.status,
        current_movie_id=db_session.current_movie_id,
        match_movie_id=db_session.match_movie_id,
        participants=[u.user_id for u in db_session.users],
        created_at=db_session.created_at
    )


@app.post("/sessions/join", response_model=schemas.SessionResponse)
async def join_session(request: schemas.SessionJoin, db: Session = Depends(get_db)):
    """
    Join an existing session by code
    """
    # Find session by code
    db_session = db.query(models.Session).filter(
        models.Session.code == request.session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if db_session.status == models.SessionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Session is completed")
    
    # Check if user is already in session
    existing_user = db.query(models.SessionUser).filter(
        models.SessionUser.session_id == db_session.id,
        models.SessionUser.user_id == request.user_id
    ).first()
    
    if existing_user:
        # Reactivate user if was inactive
        if not existing_user.is_active:
            existing_user.is_active = True
            existing_user.last_seen = datetime.utcnow()
            db.commit()
    else:
        # Add new user to session
        db_user = models.SessionUser(
            session_id=db_session.id,
            user_id=request.user_id
        )
        db.add(db_user)
        db.commit()
    
    db.refresh(db_session)
    
    return schemas.SessionResponse(
        session_id=db_session.id,
        session_code=db_session.code,
        creator_id=db_session.creator_id,
        status=db_session.status,
        current_movie_id=db_session.current_movie_id,
        match_movie_id=db_session.match_movie_id,
        participants=[u.user_id for u in db_session.users if u.is_active],
        created_at=db_session.created_at
    )


@app.get("/sessions/{session_code}/validate", response_model=schemas.ValidateSessionResponse)
async def validate_session(session_code: str, db: Session = Depends(get_db)):
    """
    Validate session and return session details
    Used by other services (Match Service, Recommendation Service)
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if db_session.status == models.SessionStatus.ABANDONED:
        raise HTTPException(status_code=400, detail="Session has been abandoned")
    
    active_users = [u.user_id for u in db_session.users if u.is_active]
    
    return schemas.ValidateSessionResponse(
        is_valid=True,
        session_id=db_session.id,
        status=db_session.status,
        participants=active_users,
        current_movie_id=db_session.current_movie_id
    )


@app.get("/sessions/{session_code}", response_model=schemas.SessionResponse)
async def get_session(session_code: str, db: Session = Depends(get_db)):
    """
    Get session details by code
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return schemas.SessionResponse(
        session_id=db_session.id,
        session_code=db_session.code,
        creator_id=db_session.creator_id,
        status=db_session.status,
        current_movie_id=db_session.current_movie_id,
        match_movie_id=db_session.match_movie_id,
        participants=[u.user_id for u in db_session.users if u.is_active],
        created_at=db_session.created_at
    )


@app.put("/sessions/{session_code}/movie", response_model=schemas.SessionResponse)
async def update_current_movie(
    session_code: str,
    request: schemas.UpdateMovieRequest,
    db: Session = Depends(get_db)
):
    """
    Update the current movie for a session
    Called by Match Service after movie selection or skip
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.current_movie_id = request.current_movie_id
    db_session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_session)
    
    return schemas.SessionResponse(
        session_id=db_session.id,
        session_code=db_session.code,
        creator_id=db_session.creator_id,
        status=db_session.status,
        current_movie_id=db_session.current_movie_id,
        match_movie_id=db_session.match_movie_id,
        participants=[u.user_id for u in db_session.users if u.is_active],
        created_at=db_session.created_at
    )


@app.put("/sessions/{session_code}/match", response_model=schemas.SessionResponse)
async def update_match(
    session_code: str,
    request: schemas.UpdateMatchRequest,
    db: Session = Depends(get_db)
):
    """
    Update the match for a session
    Called by Match Service when a match is found
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.match_movie_id = request.match_movie_id
    db_session.status = models.SessionStatus.COMPLETED
    db_session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_session)
    
    return schemas.SessionResponse(
        session_id=db_session.id,
        session_code=db_session.code,
        creator_id=db_session.creator_id,
        status=db_session.status,
        current_movie_id=db_session.current_movie_id,
        match_movie_id=db_session.match_movie_id,
        participants=[u.user_id for u in db_session.users if u.is_active],
        created_at=db_session.created_at
    )


@app.post("/sessions/{session_code}/disconnect/{user_id}")
async def disconnect_user(session_code: str, user_id: str, db: Session = Depends(get_db)):
    """
    Mark a user as disconnected from session
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_user = db.query(models.SessionUser).filter(
        models.SessionUser.session_id == db_session.id,
        models.SessionUser.user_id == user_id
    ).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found in session")
    
    db_user.is_active = False
    db.commit()
    
    return {"status": "disconnected", "session_code": session_code, "user_id": user_id}


@app.post("/sessions/{session_code}/complete")
async def complete_session(session_code: str, db: Session = Depends(get_db)):
    """
    Mark session as completed
    Called after a match is found and user decides to finish
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.status = models.SessionStatus.COMPLETED
    db_session.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "completed", "session_code": session_code}


@app.post("/sessions/{session_code}/start", response_model=schemas.SessionResponse)
async def start_session(session_code: str, db: Session = Depends(get_db)):
    """
    Start the session (change status to ACTIVE)
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if db_session.status != models.SessionStatus.WAITING:
        # If already active, just return it
        if db_session.status == models.SessionStatus.ACTIVE:
             return schemas.SessionResponse(
                session_id=db_session.id,
                session_code=db_session.code,
                creator_id=db_session.creator_id,
                status=db_session.status,
                current_movie_id=db_session.current_movie_id,
        match_movie_id=db_session.match_movie_id,
                participants=[u.user_id for u in db_session.users if u.is_active],
                created_at=db_session.created_at
            )
        raise HTTPException(status_code=400, detail="Session is not in waiting state")
        
    db_session.status = models.SessionStatus.ACTIVE
    db_session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_session)
    
    return schemas.SessionResponse(
        session_id=db_session.id,
        session_code=db_session.code,
        creator_id=db_session.creator_id,
        status=db_session.status,
        current_movie_id=db_session.current_movie_id,
        match_movie_id=db_session.match_movie_id,
        participants=[u.user_id for u in db_session.users if u.is_active],
        created_at=db_session.created_at
    )


@app.post("/sessions/{session_code}/continue", response_model=schemas.SessionResponse)
async def continue_session(session_code: str, db: Session = Depends(get_db)):
    """
    Continue session after a match (reset match state)
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db_session.match_movie_id = None
    db_session.status = models.SessionStatus.ACTIVE
    db_session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_session)
    
    return schemas.SessionResponse(
        session_id=db_session.id,
        session_code=db_session.code,
        creator_id=db_session.creator_id,
        status=db_session.status,
        current_movie_id=db_session.current_movie_id,
        match_movie_id=db_session.match_movie_id,
        participants=[u.user_id for u in db_session.users if u.is_active],
        created_at=db_session.created_at
    )


@app.post("/sessions/{session_code}/end", response_model=schemas.SessionResponse)
async def end_session(session_code: str, db: Session = Depends(get_db)):
    """
    End the session
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db_session.status = models.SessionStatus.ABANDONED
    db_session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_session)
    
    return schemas.SessionResponse(
        session_id=db_session.id,
        session_code=db_session.code,
        creator_id=db_session.creator_id,
        status=db_session.status,
        current_movie_id=db_session.current_movie_id,
        match_movie_id=db_session.match_movie_id,
        participants=[u.user_id for u in db_session.users if u.is_active],
        created_at=db_session.created_at
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
