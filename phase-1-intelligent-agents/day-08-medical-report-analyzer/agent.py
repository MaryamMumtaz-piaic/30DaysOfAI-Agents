"""AI medical report analyzer.

Given a lab/blood report as text (from a PDF) or an image (read with GPT-4o
vision), the agent:
  1. Extracts every measured marker with its value, unit, and reference range.
  2. Classifies each as normal / borderline / critical (low or high).
  3. Explains in plain English what each marker means.
  4. Identifies potential health risks and recommends next steps.

Progress is reported through an async callback so the FastAPI layer can
stream it to the browser over a WebSocket.

NOTE: This is an educational tool, not a medical diagnosis.
"""

from __future__ import annotations

import json
import os
from typing import Awaitable, Callable

from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MAX_CHARS = 20000

ProgressFn = Callable[[str, str], Awaitable[None]]

VALID_STATUS = {"normal", "borderline", "critical"}


async def _noop(stage: str, message: str) -> None:
    return None


class MedicalAgent:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def analyze(
        self,
        text: str = "",
        image_url: str = "",
        patient_context: str = "",
        progress: ProgressFn = _noop,
    ) -> dict:
        text = (text or "").strip()[:MAX_CHARS]
        if not text and not image_url:
            raise ValueError("No report provided to analyze")

        if image_url:
            await progress("start", "Reading report image with vision model")
        else:
            await progress("start", f"Analyzing report ({len(text):,} characters)")

        result = await self._analyze(text, image_url, patient_context, progress)
        await progress("done", "Analysis complete")
        return result

    async def _analyze(
        self, text: str, image_url: str, ctx: str, progress: ProgressFn
    ) -> dict:
        await progress("analyze", "Extracting markers and comparing to reference ranges")

        ctx_line = f"Patient context: {ctx}." if ctx else ""
        instruction = (
            "You are a medical laboratory analyst. Analyze the lab/blood report and "
            "return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "report_type": "e.g. Complete Blood Count, Lipid Panel",\n'
            '  "patient_summary": "3-4 sentence plain-English summary a patient can understand",\n'
            '  "overall_status": "normal|borderline|critical",\n'
            '  "stats": {"total": 0, "normal": 0, "borderline": 0, "critical": 0},\n'
            '  "markers": [\n'
            "    {\n"
            '      "name": "marker name (e.g. Hemoglobin)",\n'
            '      "value": "measured value as string",\n'
            '      "unit": "unit e.g. g/dL",\n'
            '      "reference_range": "normal range e.g. 13.5-17.5",\n'
            '      "status": "normal|borderline|critical",\n'
            '      "direction": "low|high|normal",\n'
            '      "explanation": "one plain-English sentence on what this marker means and this result"\n'
            "    }\n"
            "  ],\n"
            '  "risks": [{"risk": "potential health concern", "severity": "low|medium|high", "based_on": ["marker names"]}],\n'
            '  "recommendations": ["actionable next step / lifestyle / specialist referral"],\n'
            '  "urgent": false,\n'
            '  "urgent_note": "if urgent is true, one line on why immediate care is advised; else empty"\n'
            "}\n"
            "Compare each value to standard adult reference ranges. Mark 'critical' only for "
            "clearly out-of-range values, 'borderline' for near-limit. Set overall_status and "
            "urgent conservatively. Ensure stats counts match the markers array. "
            "Keep every explanation non-alarming and easy to understand.\n"
            f"{ctx_line}"
        )

        if image_url:
            content = [
                {"type": "text", "text": instruction + "\n\nThe report is in the attached image."},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        else:
            content = instruction + f"\n\n--- REPORT ---\n{text}"

        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": content}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content)

        data.setdefault("report_type", "Medical Report")
        data.setdefault("patient_summary", "")
        data.setdefault("overall_status", "normal")
        data.setdefault("markers", [])
        data.setdefault("risks", [])
        data.setdefault("recommendations", [])
        data.setdefault("urgent", False)
        data.setdefault("urgent_note", "")

        markers = data["markers"]
        for m in markers:
            status = str(m.get("status", "normal")).lower()
            if status not in VALID_STATUS:
                status = "normal"
            m["status"] = status
            m.setdefault("name", "")
            m.setdefault("value", "")
            m.setdefault("unit", "")
            m.setdefault("reference_range", "")
            m.setdefault("direction", "normal")
            m.setdefault("explanation", "")

        data["stats"] = {
            "total": len(markers),
            "normal": sum(1 for m in markers if m["status"] == "normal"),
            "borderline": sum(1 for m in markers if m["status"] == "borderline"),
            "critical": sum(1 for m in markers if m["status"] == "critical"),
        }

        await progress(
            "analyze",
            f"Found {data['stats']['total']} markers — "
            f"{data['stats']['critical']} critical, {data['stats']['borderline']} borderline",
        )
        return data
