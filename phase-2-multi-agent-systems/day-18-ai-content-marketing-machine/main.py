"""FastAPI server for AI Content Marketing Machine — Day 18

Routes:
  GET  /                     → Serve the single-page HTML dashboard
  GET  /presets              → Return default industry brand presets
  WS   /ws/generate          → Stream content generation pipeline
  GET  /report/{job_id}.pdf  → Download executive PDF report
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from agents import ContentMarketingSystem, INDUSTRY_PRESETS
from pdf_builder import build_content_marketing_pdf

app = FastAPI(title="AI Content Marketing Machine — Day 18")

REPORTS_DB: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# HTTP - Root Index
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def get_index() -> HTMLResponse:
    try:
        with open("static/index.html", encoding="utf-8") as fh:
            return HTMLResponse(fh.read())
    except FileNotFoundError:
        return HTMLResponse(
            "<h3>Static files not ready. Please ensure static/index.html exists.</h3>",
            status_code=404
        )

# ---------------------------------------------------------------------------
# HTTP - Presets
# ---------------------------------------------------------------------------
@app.get("/presets")
async def get_presets() -> dict:
    return INDUSTRY_PRESETS

# ---------------------------------------------------------------------------
# WebSocket - Pipeline Execution
# ---------------------------------------------------------------------------
@app.websocket("/ws/generate")
async def ws_generate(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        payload = await websocket.receive_json()

        brand_name = str(payload.get("brand_name", "Brand")).strip()
        brand_voice = str(payload.get("brand_voice", "Professional")).strip()
        target_audience = str(payload.get("target_audience", "General")).strip()
        industry = str(payload.get("industry", "Technology")).strip()
        weekly_topic = str(payload.get("weekly_topic", "General Topic")).strip()
        brand_colors = str(payload.get("brand_colors", "")).strip()
        content_pillars = payload.get("content_pillars", [])

        if not brand_name or not weekly_topic:
            await websocket.send_json({"type": "error", "message": "Brand name and weekly topic are required."})
            await websocket.close()
            return

        async def stream_progress(stage: str, message: str) -> None:
            try:
                await websocket.send_json({
                    "type": "progress",
                    "stage": stage,
                    "message": message
                })
            except Exception:
                pass

        system = ContentMarketingSystem()
        result = await system.run(
            brand_name=brand_name,
            brand_voice=brand_voice,
            target_audience=target_audience,
            industry=industry,
            weekly_topic=weekly_topic,
            brand_colors=brand_colors,
            content_pillars=content_pillars,
            progress=stream_progress
        )

        job_id = uuid.uuid4().hex
        REPORTS_DB[job_id] = result

        await websocket.send_json({
            "type": "result",
            "job_id": job_id,
            "data": result
        })

    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Content generation pipeline failed: {str(exc)}"
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

# ---------------------------------------------------------------------------
# HTTP - Download PDF
# ---------------------------------------------------------------------------
@app.get("/report/{job_id}.pdf")
async def download_pdf(job_id: str) -> Response:
    report = REPORTS_DB.get(job_id)
    if not report:
        return Response("Content marketing report not found.", status_code=404)

    try:
        pdf_bytes = build_content_marketing_pdf(report)
        brand_name = report.get("metadata", {}).get("brand_name", "marketing")
        safe_name = "".join(c if c.isalnum() else "_" for c in brand_name)[:30].lower() or "marketing"
        filename = f"marsa_content_suite_{safe_name}_{job_id[:6]}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as err:
        return Response(f"PDF creation failed: {str(err)}", status_code=500)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
