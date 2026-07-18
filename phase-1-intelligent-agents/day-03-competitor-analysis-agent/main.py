"""FastAPI server: web UI + WebSocket-streamed competitor analysis + PDF export."""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from agent import CompetitorAgent
from report import build_pdf

app = FastAPI(title="Real-Time Competitor Intelligence Agent")

# In-memory cache of finished analyses, keyed by job id (fine for a single-node demo).
REPORTS: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.websocket("/ws/analyze")
async def analyze_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()
        niche = (payload.get("niche") or "").strip()
        urls = [u for u in (payload.get("urls") or []) if u and u.strip()]

        if not niche or not urls:
            await ws.send_json(
                {"type": "error", "message": "Niche and at least one competitor URL are required"}
            )
            await ws.close()
            return

        try:
            agent = CompetitorAgent()
        except RuntimeError as exc:  # missing API key
            await ws.send_json({"type": "error", "message": str(exc)})
            await ws.close()
            return

        async def progress(stage: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage, "message": message})

        result = await agent.analyze(niche, urls, progress)

        job_id = uuid.uuid4().hex
        REPORTS[job_id] = {"niche": niche, "data": result}
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
    pdf = build_pdf(entry["niche"], entry["data"])
    safe = "".join(c if c.isalnum() else "_" for c in entry["niche"])[:40] or "report"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="competitor_{safe}.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
