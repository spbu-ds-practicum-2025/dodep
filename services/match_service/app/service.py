import httpx
import os
from models import SwipeRequest, SwipeResponse, MatchPayload, NextMoviePayload
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
        return SwipeResponse(event="error", payload={"message": "Redis unavailable"})

    key = f"session:{request.session_id}:movie:{request.movie_id}"
    
    # Logic for SKIP
    if request.swipe_value == "skip":
        # 1. Save vote (optional, but good for consistency)
        redis.hset(key, f"vote:{request.user_id}", "skip")
        
        # 2. Get next movie
        next_movie_id = await get_next_movie(request.session_id, request.movie_id)
        
        if not next_movie_id:
             return SwipeResponse(event="error", payload={"message": "Could not get next movie"})

        # 3. Update Session Service
        await update_session_movie(request.session_id, next_movie_id)
        
        # 4. Clear current movie votes
        redis.delete(key)
        
        # 5. Return next_movie event
        return SwipeResponse(
            event="next_movie",
            payload=NextMoviePayload(movie_id=next_movie_id, reason="skip")
        )

    # Logic for WANT_NOW
    elif request.swipe_value == "want_now":
        # 1. Save vote
        redis.hset(key, f"vote:{request.user_id}", "want_now")
        
        # 2. Check all votes
        # We need to know who has voted.
        # Redis HGETALL returns all fields. We filter for keys starting with "vote:"
        all_data = redis.hgetall(key)
        votes = {k: v for k, v in all_data.items() if k.startswith("vote:")}
        
        # Check if all participants have voted
        # participants is a list of user_ids
        all_voted = True
        for user in request.participants:
            if f"vote:{user}" not in votes:
                all_voted = False
                break
        
        if all_voted:
            # Check if everyone voted "want_now"
            # Since "skip" triggers immediate next movie, if we are here and everyone voted,
            # and we haven't deleted the key yet, it implies everyone voted "want_now".
            # But let's be safe and check values.
            all_want_now = all(v == "want_now" for v in votes.values())
            
            if all_want_now:
                return SwipeResponse(
                    event="match_found",
                    payload=MatchPayload(movie_id=request.movie_id, participants=request.participants)
                )
            else:
                # This state theoretically shouldn't be reached if "skip" is immediate,
                # unless there's a race condition or logic change.
                # If someone skipped, the key should be gone.
                # But if we are here, maybe handle as next movie?
                # For now, let's assume strict "skip -> immediate next" logic.
                pass
        
        # If not everyone voted yet
        return SwipeResponse(
            event="vote_recorded",
            user_id=request.user_id,
            completed=False
        )

    return SwipeResponse(event="error", payload={"message": "Invalid swipe value"})
