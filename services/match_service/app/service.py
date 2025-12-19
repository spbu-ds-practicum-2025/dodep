import httpx
import os
from models import SwipeRequest, SwipeResponse, MatchedMovie
from redis_client import get_redis_client

REC_SERVICE_URL = os.getenv("REC_SERVICE_URL", "http://recommendation-service:8000")
SESSION_SERVICE_URL = os.getenv("SESSION_SERVICE_URL", "http://session-service:8000")

async def get_next_movie(session_id: str, current_movie_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{REC_SERVICE_URL}/recommendation/next",
                params={"session_id": session_id, "current_movie_id": current_movie_id}
            )
            response.raise_for_status()
            return response.json().get("movie_id")
        except Exception as e:
            print(f"Error fetching next movie: {e}")
            return None

async def update_session_movie(session_id: str, next_movie_id: str):
    async with httpx.AsyncClient() as client:
        try:
            # Assuming Session Service has an endpoint to update the session
            response = await client.patch(
                f"{SESSION_SERVICE_URL}/sessions/{session_id}",
                json={"current_movie_id": next_movie_id}
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Error updating session movie: {e}")

async def process_swipe(request: SwipeRequest) -> SwipeResponse:
    redis = get_redis_client()
    if not redis:
        return SwipeResponse(status="error", message="Redis unavailable")

    # Ensure IDs are strings for Redis keys
    session_id_str = str(request.session_id)
    movie_id_str = str(request.movie_id)
    user_id_str = str(request.user_id)

    key = f"session:{session_id_str}:movie:{movie_id_str}"
    
    # Logic for SKIP
    if request.swipe_value == "skip":
        # 1. Save vote
        redis.hset(key, f"vote:{user_id_str}", "skip")
        
        # 2. Get next movie (Side effect)
        next_movie_id = await get_next_movie(session_id_str, movie_id_str)
        
        if next_movie_id:
             # 3. Update Session Service (Side effect)
             await update_session_movie(session_id_str, next_movie_id)
        
        # 4. Clear current movie votes
        redis.delete(key)
        
        # 5. Return next_movie status
        return SwipeResponse(
            status="next_movie",
            session_id=request.session_id,
            movie_id=request.movie_id,
            message="Not all participants wanted this movie"
        )

    # Logic for WANT_NOW
    elif request.swipe_value == "want_now":
        # 1. Save vote
        redis.hset(key, f"vote:{user_id_str}", "want_now")
        
        # 2. Check all votes
        all_data = redis.hgetall(key)
        votes = {k: v for k, v in all_data.items() if k.startswith("vote:")}
        
        votes_count = len(votes)
        required_votes = len(request.participants)
        
        # Check if all participants have voted
        all_voted = True
        for user in request.participants:
            if f"vote:{user}" not in votes:
                all_voted = False
                break
        
        if all_voted:
            # Check if everyone voted "want_now"
            all_want_now = all(v == "want_now" for v in votes.values())
            
            if all_want_now:
                return SwipeResponse(
                    status="match_found",
                    session_id=request.session_id,
                    movie_id=request.movie_id,
                    matched_movie=MatchedMovie(id=request.movie_id, title="Unknown Title")
                )
            else:
                # If there is a "skip" in votes (race condition or logic), treat as next movie
                redis.delete(key)
                return SwipeResponse(
                    status="next_movie",
                    session_id=request.session_id,
                    movie_id=request.movie_id,
                    message="Not all participants wanted this movie"
                )

        # If not everyone voted yet
        return SwipeResponse(
            status="vote_recorded",
            session_id=request.session_id,
            movie_id=request.movie_id,
            votes_count=votes_count,
            required_votes=required_votes
        )

    return SwipeResponse(status="error", message="Invalid swipe value")
