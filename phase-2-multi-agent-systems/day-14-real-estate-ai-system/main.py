"""FastAPI server: web UI + WebSocket-streamed property analysis + PDF export."""

from __future__ import annotations

import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from agent import RealEstateAnalyzer
from report import build_pdf

app = FastAPI(title="AI Real Estate Investment Analyzer")

# In-memory cache of finished analyses, keyed by job id (single-node demo).
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
        address = (payload.get("address") or "").strip()

        if len(address) < 5:
            await ws.send_json({"type": "error", "message": "Enter a property address"})
            await ws.close()
            return

        try:
            analyzer = RealEstateAnalyzer()
        except RuntimeError as exc:  # missing API key
            await ws.send_json({"type": "error", "message": str(exc)})
            await ws.close()
            return

        async def progress(stage: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage, "message": message})

        result = await analyzer.analyze(
            address=address,
            budget=payload.get("budget") or 0,
            beds=payload.get("beds") or 3,
            baths=payload.get("baths") or 2,
            sqft=payload.get("sqft") or 1500,
            property_type=payload.get("property_type") or "single-family home",
            progress=progress,
        )

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
    address = entry["data"].get("property", {}).get("address", "property")
    safe = "".join(c if c.isalnum() else "_" for c in address)[:40] or "property"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="realestate_{safe}.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
