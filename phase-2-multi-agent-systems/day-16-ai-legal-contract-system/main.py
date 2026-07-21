"""FastAPI server for AI Legal Contract System — Day 16

Routes:
  GET  /                     → Serve the single-page HTML app
  GET  /templates            → Return contract template metadata
  WS   /ws/generate          → Stream contract generation progress
  GET  /report/{job_id}.pdf  → Download the signed-ready PDF
"""

from __future__ import annotations

import json
import os
import uuid
from io import BytesIO
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from agents import LegalContractSystem, CONTRACT_TEMPLATES
from pdf_builder import build_contract_pdf

app = FastAPI(title="AI Legal Contract System — Day 16")

# In-memory report store (single-node demo)
REPORTS: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# HTML page
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


# ---------------------------------------------------------------------------
# Template metadata endpoint
# ---------------------------------------------------------------------------

@app.get("/templates")
async def get_templates() -> dict:
    return {
        key: {
            "name": tpl["name"],
            "fields": tpl["fields"],
        }
        for key, tpl in CONTRACT_TEMPLATES.items()
    }


# ---------------------------------------------------------------------------
# WebSocket — contract generation pipeline
# ---------------------------------------------------------------------------

@app.websocket("/ws/generate")
async def generate_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()

        # Validate required fields
        required = ["contract_type", "party_a", "party_b", "jurisdiction", "duration", "purpose"]
        missing = [f for f in required if not str(payload.get(f, "")).strip()]
        if missing:
            await ws.send_json({
                "type": "error",
                "message": f"Missing required fields: {', '.join(missing)}"
            })
            await ws.close()
            return

        contract_type = str(payload["contract_type"]).strip()
        party_a       = str(payload["party_a"]).strip()
        party_b       = str(payload["party_b"]).strip()
        jurisdiction  = str(payload["jurisdiction"]).strip()
        duration      = str(payload["duration"]).strip()
        purpose       = str(payload["purpose"]).strip()
        extra_clauses = str(payload.get("extra_clauses", "")).strip()

        async def progress(stage: str, message: str) -> None:
            try:
                await ws.send_json({"type": "progress", "stage": stage, "message": message})
            except Exception:
                pass

        system = LegalContractSystem()
        result = await system.run(
            contract_type=contract_type,
            party_a=party_a,
            party_b=party_b,
            jurisdiction=jurisdiction,
            duration=duration,
            purpose=purpose,
            extra_clauses=extra_clauses,
            progress=progress,
        )

        job_id = uuid.uuid4().hex
        REPORTS[job_id] = result

        await ws.send_json({
            "type": "result",
            "job_id": job_id,
            "data": result,
        })

    except WebSocketDisconnect:
        return
    except RuntimeError as exc:
        # Catches missing API key and similar setup errors
        try:
            await ws.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
    except Exception as exc:
        try:
            await ws.send_json({"type": "error", "message": f"Unexpected error: {str(exc)}"})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# PDF download
# ---------------------------------------------------------------------------

@app.get("/report/{job_id}.pdf")
async def download_pdf(job_id: str) -> Response:
    report = REPORTS.get(job_id)
    if report is None:
        return Response("Report not found — it may have expired.", status_code=404)

    pdf_bytes = build_contract_pdf(report)

    ctype = report.get("contract_type", "contract")
    safe = "".join(c if c.isalnum() else "_" for c in ctype)[:30] or "contract"
    filename = f"legal_contract_{safe}_{job_id[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Static files (mounted last so routes take priority)
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="static"), name="static")
