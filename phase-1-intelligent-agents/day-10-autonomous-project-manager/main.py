"""FastAPI server: web UI + WebSocket-streamed project planning + PDF export."""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from agent import ProjectManagerAgent
from report import build_pdf

app = FastAPI(title="Autonomous AI Project Manager")

# In-memory cache of finished plans, keyed by job id (single-node demo).
REPORTS: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.websocket("/ws/plan")
async def plan_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()
        goal = (payload.get("goal") or "").strip()
        team_size = payload.get("team_size") or 3
        deadline_weeks = payload.get("deadline_weeks") or 0

        if len(goal) < 8:
            await ws.send_json(
                {"type": "error", "message": "Describe your project goal in a sentence"}
            )
            await ws.close()
            return

        try:
            agent = ProjectManagerAgent()
        except RuntimeError as exc:  # missing API key
            await ws.send_json({"type": "error", "message": str(exc)})
            await ws.close()
            return

        async def progress(stage: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage, "message": message})

        result = await agent.plan(goal, team_size, deadline_weeks, progress)

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
    title = entry["data"].get("title", "project_plan")
    safe = "".join(c if c.isalnum() else "_" for c in title)[:40] or "project_plan"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="plan_{safe}.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
