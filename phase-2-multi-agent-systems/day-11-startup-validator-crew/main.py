"""FastAPI server: web UI + WebSocket-streamed startup validation + PDF export."""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from agent import StartupValidatorCrew
from report import build_pdf

app = FastAPI(title="AI Startup Validator Crew")

# In-memory cache of finished validations, keyed by job id (single-node demo).
REPORTS: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.websocket("/ws/validate")
async def validate_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()
        idea = (payload.get("idea") or "").strip()
        industry = (payload.get("industry") or "").strip()
        stage = (payload.get("stage") or "idea").strip()

        if len(idea) < 8:
            await ws.send_json(
                {"type": "error", "message": "Describe your startup idea in a sentence"}
            )
            await ws.close()
            return

        try:
            crew = StartupValidatorCrew()
        except RuntimeError as exc:  # missing API key
            await ws.send_json({"type": "error", "message": str(exc)})
            await ws.close()
            return

        async def progress(stage_name: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage_name, "message": message})

        result = await crew.validate(idea, industry, stage, progress)

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
    idea = entry["data"].get("idea", "startup")
    safe = "".join(c if c.isalnum() else "_" for c in idea)[:40] or "startup"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="validation_{safe}.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
