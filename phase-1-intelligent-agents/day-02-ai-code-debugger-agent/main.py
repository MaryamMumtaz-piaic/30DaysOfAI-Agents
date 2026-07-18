"""FastAPI server: web UI + code analysis endpoint."""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import CodeDebuggerAgent

app = FastAPI(title="AI Code Debugger & Optimizer Agent")


class AnalyzeRequest(BaseModel):
    code: str
    language: str = "auto"


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> JSONResponse:
    try:
        agent = CodeDebuggerAgent()
    except RuntimeError as exc:  # missing API key
        return JSONResponse({"error": str(exc)}, status_code=400)

    try:
        result = await agent.analyze(req.code, req.language)
        return JSONResponse(result)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


app.mount("/static", StaticFiles(directory="static"), name="static")
