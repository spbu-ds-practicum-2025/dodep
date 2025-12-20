from fastapi import FastAPI, Depends, HTTPException, Query, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import string
import random
import httpx
from datetime import datetime, timedelta
from . import models, schemas, database

app = FastAPI(title="Session Service")

MATCH_SERVICE_URL = os.getenv("MATCH_SERVICE_URL", "http://match-service:8000")

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


@app.post("/sessions/{session_code}/vote")
async def user_voted(session_code: str, request: schemas.VoteRequest, db: Session = Depends(get_db)):
    """
    Mark user as having voted (waiting status)
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Only mark as voted if the movie matches the current session movie
    # This prevents race conditions where a vote for a previous movie marks the user as voted for the new one
    if db_session.current_movie_id != request.movie_id:
        # Just ignore, or return a warning?
        # Returning ok is fine, as the user is technically active, but we don't want to set has_voted=True for the new movie
        return {"status": "ignored", "reason": "movie_mismatch"}
        
    db_user = db.query(models.SessionUser).filter(
        models.SessionUser.session_id == db_session.id,
        models.SessionUser.user_id == request.user_id
    ).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found in session")
        
    db_user.has_voted = True
    db_user.last_seen = datetime.utcnow()
    db.commit()
    
    return {"status": "ok"}


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


async def notify_match_service_check(session_id: str, current_movie_id: int, participants: List[str]):
    """
    Notify Match Service to check if the session can proceed with the new participant list
    """
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{MATCH_SERVICE_URL}/matches/check_status",
                json={
                    "session_id": session_id,
                    "current_movie_id": current_movie_id,
                    "participants": participants
                }
            )
        except Exception as e:
            print(f"Error notifying match service: {e}")


@app.get("/sessions/{session_code}", response_model=schemas.SessionResponse)
async def get_session(
    session_code: str, 
    db: Session = Depends(get_db)
):
    """
    Get session details by code (Read-only)
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


@app.post("/sessions/{session_code}", response_model=schemas.SessionResponse)
async def session_heartbeat(
    session_code: str, 
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = Header(None, alias="user_id"), 
    db: Session = Depends(get_db)
):
    """
    Heartbeat: Update last_seen and check for timeouts
    """
    # Find session by code with lock to prevent race conditions
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).with_for_update().first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update last_seen for current user
    if user_id is not None:
        current_user = next((u for u in db_session.users if u.user_id == user_id), None)
        if current_user:
            # print(f"Updating last_seen for user {user_id}")
            current_user.last_seen = datetime.utcnow()
            current_user.is_active = True
        else:
            print(f"User {user_id} not found in session {session_code}. Users: {[u.user_id for u in db_session.users]}")
    else:
        print(f"No user_id header provided for session {session_code}")
    
    # Check for timeouts (40 seconds)
    timeout_threshold = datetime.utcnow() - timedelta(seconds=40)
    users_changed = False
    
    # print(f"Checking timeouts. Threshold: {timeout_threshold}")
    for user in db_session.users:
        # print(f"User {user.user_id}: active={user.is_active}, last_seen={user.last_seen}")
        if user.is_active and user.last_seen and user.last_seen < timeout_threshold:
            print(f"Kicking user {user.user_id} (last_seen: {user.last_seen})")
            user.is_active = False
            users_changed = True
            
            # If the kicked user was the creator, assign a new creator
            if user.user_id == db_session.creator_id:
                # Find another active user
                new_creator = next((u for u in db_session.users if u.is_active and u.user_id != user.user_id), None)
                if new_creator:
                    db_session.creator_id = new_creator.user_id
                    print(f"Creator changed from {user.user_id} to {new_creator.user_id}")
                else:
                    # No active users left, maybe abandon session?
                    # For now, just leave it, or set status to ABANDONED
                    pass
            
    if user_id or users_changed:
        db.commit()
        db.refresh(db_session)
        
    if users_changed and db_session.current_movie_id:
        # Notify Match Service to re-evaluate votes with new participant list
        active_participants = [u.user_id for u in db_session.users if u.is_active]
        background_tasks.add_task(
            notify_match_service_check, 
            db_session.code, 
            db_session.current_movie_id, 
            active_participants
        )
    
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
    
    # Reset has_voted for all users
    for user in db_session.users:
        user.has_voted = False
        
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
async def continue_session(
    session_code: str, 
    request: schemas.ContinueSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Continue session after a match (reset match state and set next movie)
    """
    db_session = db.query(models.Session).filter(
        models.Session.code == session_code
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db_session.match_movie_id = None
    db_session.current_movie_id = request.next_movie_id
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
