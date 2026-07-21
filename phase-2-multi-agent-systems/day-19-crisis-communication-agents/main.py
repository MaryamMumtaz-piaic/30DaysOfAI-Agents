import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any

from agents import run_crisis_communication_pipeline
from pdf_builder import generate_crisis_report_pdf

app = FastAPI(
    title="Day 19 - AI Crisis Communication & Brand Protection Agent",
    description="Multi-Agent Crisis Communication Engine by Maryam Mumtaz",
    version="1.0.0"
)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Memory store for recent analyses
analysis_store: Dict[str, Any] = {}

class CrisisAnalysisRequest(BaseModel):
    brand_name: str
    incident_context: str

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Day 19 AI Crisis Communication System Running</h1>")

@app.post("/api/analyze")
async def analyze_crisis(req: CrisisAnalysisRequest):
    if not req.brand_name.strip() or not req.incident_context.strip():
        raise HTTPException(status_code=400, detail="Brand name and incident description are required.")
    
    try:
        results = await run_crisis_communication_pipeline(
            brand_name=req.brand_name.strip(),
            incident_context=req.incident_context.strip()
        )
        # Store latest result
        analysis_store["latest"] = results
        return JSONResponse(content={"status": "success", "data": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf")
async def download_pdf():
    latest = analysis_store.get("latest")
    if not latest:
        raise HTTPException(status_code=404, detail="No active crisis report found. Please run an analysis first.")
    
    pdf_bytes = generate_crisis_report_pdf(latest)
    brand = latest.get("brand_name", "brand").replace(" ", "_").lower()
    filename = f"Crisis_Mitigation_Brief_{brand}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8019, reload=True)
