"""FastAPI server for AI Supply Chain Risk & Optimizer — Day 17

Routes:
  GET  /                     → Serve the single-page HTML dashboard
  GET  /presets              → Return default industry supply chain presets (BOM & Suppliers)
  WS   /ws/optimize          → Stream optimization pipeline and output reports
  GET  /report/{job_id}.pdf  → Download a professional executive PDF summary report
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

from agents import SupplyChainSystem, INDUSTRY_PRESETS
from pdf_builder import build_supply_chain_pdf

app = FastAPI(title="AI Supply Chain Risk & Optimizer — Day 17")

# In-memory session database to store final reports for PDF retrieval
REPORTS_DB: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# HTTP - Root index
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def get_index() -> HTMLResponse:
    try:
        with open("static/index.html", encoding="utf-8") as fh:
            return HTMLResponse(fh.read())
    except FileNotFoundError:
        return HTMLResponse(
            "<h3>Static files not ready yet. Please ensure static/index.html is created.</h3>",
            status_code=404
        )

# ---------------------------------------------------------------------------
# HTTP - Preset Industries Data
# ---------------------------------------------------------------------------
@app.get("/presets")
async def get_presets() -> dict:
    return INDUSTRY_PRESETS

# ---------------------------------------------------------------------------
# WebSocket - Supply Chain Multi-Agent Execution & Logs Streaming
# ---------------------------------------------------------------------------
@app.websocket("/ws/optimize")
async def ws_optimize(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        # Receive BOM and supplier configuration from the user
        payload = await websocket.receive_json()
        
        product_name = str(payload.get("product_name", "Custom Product")).strip()
        bom = payload.get("bom", [])
        suppliers = payload.get("suppliers", [])
        
        # Validation checks
        if not product_name:
            await websocket.send_json({"type": "error", "message": "Product name is required."})
            await websocket.close()
            return
        if not bom:
            await websocket.send_json({"type": "error", "message": "Bill of Materials (BOM) cannot be empty."})
            await websocket.close()
            return
        if not suppliers:
            await websocket.send_json({"type": "error", "message": "Supplier list is required."})
            await websocket.close()
            return

        # Logger function to pipe progress updates directly to the frontend
        async def stream_progress(stage: str, message: str) -> None:
            try:
                await websocket.send_json({
                    "type": "progress",
                    "stage": stage,
                    "message": message
                })
            except Exception:
                pass

        # Instantiate supply chain system and execute
        system = SupplyChainSystem()
        result = await system.run(
            product_name=product_name,
            bom=bom,
            suppliers=suppliers,
            progress=stream_progress
        )

        # Store the report in our mock database
        job_id = uuid.uuid4().hex
        REPORTS_DB[job_id] = result

        # Send final optimization result with the download job_id
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
                "message": f"Optimization pipeline failed: {str(exc)}"
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

# ---------------------------------------------------------------------------
# HTTP - Download PDF Report
# ---------------------------------------------------------------------------
@app.get("/report/{job_id}.pdf")
async def download_pdf(job_id: str) -> Response:
    report = REPORTS_DB.get(job_id)
    if not report:
        return Response("Supply chain report not found. It may have expired or server restarted.", status_code=404)

    try:
        pdf_bytes = build_supply_chain_pdf(report)
        
        prod_name = report.get("metadata", {}).get("product_name", "supply_chain")
        safe_name = "".join(c if c.isalnum() else "_" for c in prod_name)[:30].lower() or "supply_chain"
        filename = f"marsa_supply_chain_{safe_name}_{job_id[:6]}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as err:
        return Response(f"PDF creation failed: {str(err)}", status_code=500)

# ---------------------------------------------------------------------------
# Static files routing (Must be registered last to avoid routing overlaps)
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
