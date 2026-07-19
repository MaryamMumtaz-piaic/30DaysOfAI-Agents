"""FastAPI server: web UI + report extraction + WS-streamed analysis + PDF export."""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from agent import MedicalAgent
from extract import extract as extract_report
from report import build_pdf

app = FastAPI(title="AI Medical Report Analyzer")

# In-memory cache of finished analyses, keyed by job id (single-node demo).
REPORTS: dict[str, dict] = {}

MAX_UPLOAD = 12 * 1024 * 1024  # 12 MB


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.post("/extract")
async def extract_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    """Pull text or an image data URL out of an uploaded report."""
    raw = await file.read()
    if len(raw) > MAX_UPLOAD:
        return JSONResponse({"error": "File exceeds 12 MB limit"}, status_code=413)
    try:
        out = extract_report(file.filename or "", raw)
    except Exception as exc:
        return JSONResponse({"error": f"Could not read file: {exc}"}, status_code=422)

    if out["kind"] == "text":
        text = (out["text"] or "").strip()
        if len(text) < 20:
            return JSONResponse(
                {"error": "No extractable text found. For scanned reports, upload an image instead."},
                status_code=422,
            )
        out["text"] = text
    return JSONResponse({"filename": file.filename, **out})


@app.websocket("/ws/analyze")
async def analyze_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()
        text = (payload.get("text") or "").strip()
        image_url = (payload.get("image_url") or "").strip()
        patient_context = (payload.get("patient_context") or "").strip()

        if not text and not image_url:
            await ws.send_json({"type": "error", "message": "Please upload or paste a report"})
            await ws.close()
            return

        try:
            agent = MedicalAgent()
        except RuntimeError as exc:  # missing API key
            await ws.send_json({"type": "error", "message": str(exc)})
            await ws.close()
            return

        async def progress(stage: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage, "message": message})

        result = await agent.analyze(text, image_url, patient_context, progress)

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
    rtype = entry["data"].get("report_type", "report")
    safe = "".join(c if c.isalnum() else "_" for c in rtype)[:40] or "report"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="medical_{safe}.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
