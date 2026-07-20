"""FastAPI server: web UI + WebSocket-streamed email triage + mock send + PDF export."""

from __future__ import annotations

import asyncio
import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import EmailTriageAgent
from gmail import GmailError, fetch_unread, send_reply
from report import build_pdf
from sample_inbox import SAMPLE_EMAILS

app = FastAPI(title="Smart Email Triage & Auto-Response Agent")

# In-memory cache of finished triage runs, keyed by job id (single-node demo).
REPORTS: dict[str, dict] = {}


class ConnectRequest(BaseModel):
    email: str = ""
    app_password: str = ""
    limit: int = 15


class SendRequest(BaseModel):
    to: str = ""
    subject: str = ""
    body: str = ""
    # Credentials of the connected account (needed for real SMTP send).
    email: str = ""
    app_password: str = ""
    in_reply_to: str = ""


class RegenerateRequest(BaseModel):
    from_: str = ""
    subject: str = ""
    body: str = ""
    user_name: str = ""
    tone: str = ""


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.get("/sample")
async def sample() -> JSONResponse:
    """Return the demo inbox so the UI can be tried without Gmail OAuth."""
    return JSONResponse({"emails": SAMPLE_EMAILS})


@app.post("/connect")
async def connect(req: ConnectRequest) -> JSONResponse:
    """Log into Gmail via IMAP and return the most recent unread emails.

    Uses a Gmail App Password. Credentials are used for this request only and
    are never stored server-side — the browser keeps them for the send step.
    """
    user = req.email.strip()
    pwd = req.app_password.replace(" ", "").strip()
    if not user or not pwd:
        return JSONResponse({"error": "Email and App Password are required."}, status_code=400)

    limit = max(1, min(50, req.limit or 15))
    try:
        emails = await asyncio.to_thread(fetch_unread, user, pwd, limit)
    except GmailError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        return JSONResponse({"error": f"Unexpected error: {exc}"}, status_code=500)

    return JSONResponse({"emails": emails, "count": len(emails), "account": user})


@app.websocket("/ws/triage")
async def triage_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        payload = await ws.receive_json()
        emails = payload.get("emails") or []
        user_name = (payload.get("user_name") or "").strip()

        emails = [e for e in emails if e.get("subject") or e.get("body")]
        if not emails:
            await ws.send_json(
                {"type": "error", "message": "No emails to triage — load the sample or paste an email"}
            )
            await ws.close()
            return

        try:
            agent = EmailTriageAgent()
        except RuntimeError as exc:  # missing API key
            await ws.send_json({"type": "error", "message": str(exc)})
            await ws.close()
            return

        async def progress(stage: str, message: str) -> None:
            await ws.send_json({"type": "progress", "stage": stage, "message": message})

        result = await agent.triage(emails, user_name, progress)

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


@app.post("/send")
async def send(req: SendRequest) -> JSONResponse:
    """Send the approved reply.

    If the connected account's credentials are provided, the reply is delivered
    for real via Gmail SMTP. Otherwise it falls back to a demo (no-op) send so
    the sample inbox can still be tried end-to-end.
    """
    if not req.body.strip():
        return JSONResponse({"error": "Empty reply body"}, status_code=400)

    user = req.email.strip()
    pwd = req.app_password.replace(" ", "").strip()

    if not user or not pwd:
        return JSONResponse(
            {"status": "sent", "to": req.to, "subject": req.subject,
             "message": f"Reply queued to {req.to or 'recipient'} (demo — connect Gmail to deliver for real)."}
        )

    try:
        await asyncio.to_thread(
            send_reply, user, pwd, req.to, req.subject, req.body, req.in_reply_to
        )
    except GmailError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        return JSONResponse({"error": f"Unexpected error: {exc}"}, status_code=500)

    return JSONResponse(
        {"status": "sent", "to": req.to, "subject": req.subject,
         "message": f"Reply delivered to {req.to or 'recipient'} via Gmail."}
    )


@app.post("/regenerate")
async def regenerate(req: RegenerateRequest) -> JSONResponse:
    """Generate a fresh AI reply draft for one email."""
    try:
        agent = EmailTriageAgent()
    except RuntimeError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    email_obj = {"from": req.from_, "subject": req.subject, "body": req.body}
    try:
        reply = await agent.draft_reply(email_obj, req.user_name, req.tone)
    except Exception as exc:
        return JSONResponse({"error": f"Could not regenerate: {exc}"}, status_code=500)
    return JSONResponse({"draft_reply": reply})


@app.get("/report/{job_id}.pdf")
async def download_pdf(job_id: str) -> Response:
    entry = REPORTS.get(job_id)
    if entry is None:
        return Response("Report not found", status_code=404)
    pdf = build_pdf(entry["data"])
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="inbox_triage.pdf"'},
    )


app.mount("/static", StaticFiles(directory="static"), name="static")
