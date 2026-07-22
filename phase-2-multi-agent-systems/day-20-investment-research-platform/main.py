import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any

from agents import run_investment_research

app = FastAPI(
    title="Day 20 - AI Investment Research Platform",
    description="Multi-Agent Hedge Fund Terminal by Maryam Mumtaz",
    version="1.0.0"
)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

class ResearchRequest(BaseModel):
    ticker: str

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Day 20 AI Investment System Running</h1>")

@app.post("/api/research")
async def analyze_stock(req: ResearchRequest):
    if not req.ticker.strip():
        raise HTTPException(status_code=400, detail="Stock ticker is required.")
    
    try:
        results = await run_investment_research(ticker=req.ticker.strip().upper())
        return JSONResponse(content={"status": "success", "data": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8020, reload=True)
