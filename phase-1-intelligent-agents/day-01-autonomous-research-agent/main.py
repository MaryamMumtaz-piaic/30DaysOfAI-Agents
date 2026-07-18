"""FastAPI server: web UI, WebSocket progress streaming, and PDF download."""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from agent import ResearchAgent, ResearchResult
from report import build_pdf

app = FastAPI(title="Autonomous Deep Research Agent")

# In-memory cache of finished reports, keyed by job id (fine for a single-node demo).
REPORTS: dict[str, ResearchResult] = {}


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.websocket("/ws/research")
async def research_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()
        topic = (payload.get("topic") or "").strip()
        if not topic:
            await ws.send_json({"type": "error", "message": "Topic is required"})
            await ws.close()
            return

        try:
            agent = ResearchAgent()
        except RuntimeError as exc:  # missing API keys
            await ws.send_json({"type": "error", "message": str(exc)})
            await ws.close()
            return

        async def progress(stage: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage, "message": message})

        result = await agent.research(topic, progress)

        job_id = uuid.uuid4().hex
        REPORTS[job_id] = result
        await ws.send_json(
            {"type": "result", "job_id": job_id, "data": result.to_dict()}
        )
    except WebSocketDisconnect:
        return
    except Exception as exc:  # surface unexpected failures to the UI
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
    result = REPORTS.get(job_id)
    if result is None:
        return Response("Report not found", status_code=404)
    pdf = build_pdf(result)
    safe = "".join(c if c.isalnum() else "_" for c in result.topic)[:40] or "report"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe}.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
