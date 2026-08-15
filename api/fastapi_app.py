"""
FastAPI Server Proxy
Provides server-side /api/gemini endpoint to keep API keys secure.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests

app = FastAPI(title="IPL Analytics Backend Proxy API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GeminiRequest(BaseModel):
    prompt: str
    model: str = "gemini-3.5-flash-lite"


@app.post("/api/gemini")
async def proxy_gemini_request(req: GeminiRequest):
    """Server-side proxy forwarding AI requests to Gemini API securely."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable not configured on server.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{req.model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": req.prompt}]}]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
