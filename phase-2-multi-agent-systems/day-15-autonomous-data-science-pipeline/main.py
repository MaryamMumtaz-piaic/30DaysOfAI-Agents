"""FastAPI server: web UI + WebSocket-streamed ML pipeline + PDF export."""

from __future__ import annotations

import base64
import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from pipeline import DataSciencePipeline
from report import build_pdf

app = FastAPI(title="Autonomous Data Science Pipeline")

# In-memory cache of finished runs, keyed by job id (single-node demo).
REPORTS: dict[str, dict] = {}

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.websocket("/ws/run")
async def run_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()
        b64 = payload.get("csv_b64") or ""
        target = (payload.get("target") or "").strip()

        if not b64:
            await ws.send_json({"type": "error", "message": "Upload a CSV file first"})
            await ws.close()
            return

        try:
            csv_bytes = base64.b64decode(b64)
        except Exception:
            await ws.send_json({"type": "error", "message": "Could not decode the uploaded file"})
            await ws.close()
            return

        if len(csv_bytes) > MAX_UPLOAD_BYTES:
            await ws.send_json({"type": "error", "message": "File too large (max 15 MB)"})
            await ws.close()
            return

        pipeline = DataSciencePipeline()

        async def progress(stage: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage, "message": message})

        result = await pipeline.run(csv_bytes, target, progress)

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


@app.websocket("/ws/columns")
async def columns_ws(ws: WebSocket) -> None:
    """Peek at a CSV's header + inferred target so the UI can offer a picker."""
    await ws.accept()
    try:
        payload = await ws.receive_json()
        b64 = payload.get("csv_b64") or ""
        csv_bytes = base64.b64decode(b64)
        import io

        import pandas as pd

        df = pd.read_csv(io.BytesIO(csv_bytes), nrows=200)
        cols = [str(c).strip() for c in df.columns]
        await ws.send_json({
            "type": "columns",
            "columns": cols,
            "suggested": cols[-1] if cols else "",
            "rows_preview": int(len(df)),
        })
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
    target = entry["data"].get("target", "dataset")
    safe = "".join(c if c.isalnum() else "_" for c in target)[:40] or "dataset"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ml_report_{safe}.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
