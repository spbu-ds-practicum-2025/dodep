from fastapi import FastAPI, HTTPException
from models import SwipeRequest, SwipeResponse
from service import process_swipe

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

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Match Service is running"}
