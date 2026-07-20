"""FastAPI server: web UI + WebSocket-streamed e-commerce management + PDF export."""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from agent import EcommerceManager
from report import build_pdf

app = FastAPI(title="Autonomous E-Commerce Operations Manager")

# In-memory cache of finished runs, keyed by job id (single-node demo).
REPORTS: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.websocket("/ws/manage")
async def manage_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()
        catalog = payload.get("catalog") or []

        if not isinstance(catalog, list) or not catalog:
            await ws.send_json(
                {"type": "error", "message": "Add at least one product to the catalog"}
            )
            await ws.close()
            return

        try:
            manager = EcommerceManager()
        except RuntimeError as exc:  # missing API key
            await ws.send_json({"type": "error", "message": str(exc)})
            await ws.close()
            return

        async def progress(stage: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage, "message": message})

        result = await manager.run(catalog, progress)

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
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="ecommerce_operations.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
