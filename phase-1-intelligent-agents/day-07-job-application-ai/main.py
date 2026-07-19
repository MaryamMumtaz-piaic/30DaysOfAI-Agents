"""FastAPI server: web UI + resume extraction + WS-streamed analysis + PDF export."""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from agent import JobApplicationAgent
from extract import extract_text
from report import build_pdf

app = FastAPI(title="AI Job Application Automation Agent")

# In-memory cache of finished analyses, keyed by job id (single-node demo).
REPORTS: dict[str, dict] = {}

MAX_UPLOAD = 8 * 1024 * 1024  # 8 MB


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> JSONResponse:
    """Pull plain text out of an uploaded resume (PDF/TXT)."""
    raw = await file.read()
    if len(raw) > MAX_UPLOAD:
        return JSONResponse({"error": "File exceeds 8 MB limit"}, status_code=413)
    try:
        text = extract_text(file.filename or "", raw)
    except Exception as exc:
        return JSONResponse({"error": f"Could not read file: {exc}"}, status_code=422)

    text = (text or "").strip()
    if len(text) < 40:
        return JSONResponse(
            {"error": "No extractable text found (scanned/image PDFs are not supported)"},
            status_code=422,
        )
    return JSONResponse({"filename": file.filename, "text": text, "chars": len(text)})


@app.websocket("/ws/analyze")
async def analyze_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()
        resume = (payload.get("resume") or "").strip()
        job = (payload.get("job") or "").strip()
        num_questions = payload.get("num_questions") or 20

        if len(resume) < 40:
            await ws.send_json({"type": "error", "message": "Please provide your resume"})
            await ws.close()
            return
        if len(job) < 40:
            await ws.send_json({"type": "error", "message": "Please provide the job description"})
            await ws.close()
            return

        try:
            agent = JobApplicationAgent()
        except RuntimeError as exc:  # missing API key
            await ws.send_json({"type": "error", "message": str(exc)})
            await ws.close()
            return

        async def progress(stage: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage, "message": message})

        result = await agent.analyze(resume, job, num_questions, progress)

        job_id = uuid.uuid4().hex
        REPORTS[job_id] = {"data": result}
        await ws.send_json({"type": "result", "job_id": job_id, "data": result})
    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await ws.send_json({"type": "error", "message": str(exc)})
        except RuntimeError:
            pass
    finally:
        try:
            await ws.close()
        except RuntimeError:
            pass


@app.get("/report/{job_id}.pdf")
async def download_pdf(job_id: str) -> Response:
    entry = REPORTS.get(job_id)
    if entry is None:
        return Response("Report not found", status_code=404)
    pdf = build_pdf(entry["data"])
    title = entry["data"].get("job", {}).get("title", "application")
    safe = "".join(c if c.isalnum() else "_" for c in title)[:40] or "application"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="application_{safe}.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
