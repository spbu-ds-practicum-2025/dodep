from fastapi import FastAPI, HTTPException
from models import SwipeRequest, SwipeResponse, CheckStatusRequest
from service import process_swipe, continue_match_session, check_match_status

app = FastAPI(title="Match Service")

@app.get("/")
async def root():
    return {"message": "Match Service is running", "docs": "/docs"}

@app.post("/swipe", response_model=SwipeResponse)
async def swipe(request: SwipeRequest):
    try:
        response = await process_swipe(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/matches/check_status", response_model=SwipeResponse)
async def check_status(request: CheckStatusRequest):
    try:
        response = await check_match_status(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/matches/{session_id}/continue")
async def continue_session_endpoint(session_id: str):
    try:
        response = await continue_match_session(session_id)
        if not response:
             raise HTTPException(status_code=500, detail="Failed to continue session")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Match Service is running"}
