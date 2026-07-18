"""AI legal document analyzer & risk auditor.

Given the raw text of a legal document (contract, NDA, terms of service),
the agent:
  1. Detects the document type and produces a plain-English summary.
  2. Performs clause-by-clause analysis, scoring each clause's risk
     (green / yellow / red) from the reader's perspective.
  3. Flags missing standard protections a document of this type should have.
  4. Proposes concrete redline edits with a legal rationale for each.

Progress is reported through an async callback so the FastAPI layer can
stream it to the browser over a WebSocket.
"""

from __future__ import annotations

import json
import os
from typing import Awaitable, Callable

from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Cap the amount of document text sent to the model (keeps latency/cost sane).
MAX_CHARS = 24000

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


class LegalAgent:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def analyze(
        self,
        text: str,
        doc_type: str = "",
        party: str = "",
        progress: ProgressFn = _noop,
    ) -> dict:
        text = (text or "").strip()
        if len(text) < 40:
            raise ValueError("Document text is too short to analyze")

        truncated = len(text) > MAX_CHARS
        if truncated:
            text = text[:MAX_CHARS]

        label = doc_type or "document"
        await progress("start", f"Analyzing {label} ({len(text):,} characters)")
        if truncated:
            await progress(
                "start", f"Document is long — analyzing the first {MAX_CHARS:,} characters"
            )

        result = await self._synthesize(text, doc_type, party, progress)
        await progress("done", "Legal risk analysis complete")
        result["truncated"] = truncated
        return result

    async def _synthesize(
        self, text: str, doc_type: str, party: str, progress: ProgressFn
    ) -> dict:
        await progress("analyze", "Reading clauses and scoring legal risk")

        hint = f"The user says this is a: {doc_type}." if doc_type else ""
        perspective = (
            f"Analyze risk from the perspective of the '{party}'."
            if party
            else "Analyze risk from the perspective of the party signing/accepting the document."
        )

        prompt = (
            "You are a senior contracts attorney performing a risk audit. "
            "Read the legal document below and return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "doc_type": "detected document type (e.g. Mutual NDA, SaaS Terms of Service)",\n'
            '  "summary": "3-4 sentence plain-English summary of what this document does",\n'
            '  "overall_risk_score": 0-100,\n'
            '  "risk_level": "low|medium|high",\n'
            '  "party_analyzed": "whose perspective the risk is scored from",\n'
            '  "stats": {"clauses_reviewed": 0, "red": 0, "yellow": 0, "green": 0, "missing": 0},\n'
            '  "clauses": [\n'
            "    {\n"
            '      "title": "short clause name (e.g. Limitation of Liability)",\n'
            '      "excerpt": "a short verbatim quote from the clause (<=200 chars)",\n'
            '      "risk": "green|yellow|red",\n'
            '      "risk_score": 0-100,\n'
            '      "issue": "what makes this clause risky or notable (one sentence)",\n'
            '      "recommendation": "what to change or negotiate (one sentence)"\n'
            "    }\n"
            "  ],\n"
            '  "missing_clauses": [\n'
            '    {"name": "standard clause that is absent", "importance": "high|medium|low",\n'
            '     "rationale": "why a document of this type should include it"}\n'
            "  ],\n"
            '  "recommended_edits": [\n'
            '    {"clause": "clause name", "original": "problematic original wording",\n'
            '     "improved": "suggested replacement wording", "rationale": "legal reason for the change"}\n'
            "  ],\n"
            '  "red_flags": ["the single most dangerous issues, plain English"]\n'
            "}\n"
            "Rules: risk is scored for the signing party — 'red' = clearly unfavorable/dangerous, "
            "'yellow' = worth negotiating, 'green' = standard/fair. Higher overall_risk_score = MORE risk. "
            "Keep every string concise. Ensure the stats counts match the clause list you return.\n"
            f"{hint} {perspective}\n\n"
            f"--- DOCUMENT START ---\n{text}\n--- DOCUMENT END ---"
        )

        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        data = json.loads(resp.choices[0].message.content)

        data.setdefault("doc_type", doc_type or "Unknown")
        data.setdefault("summary", "")
        data.setdefault("overall_risk_score", 0)
        data.setdefault("risk_level", "medium")
        data.setdefault("party_analyzed", party or "Signing party")
        data.setdefault("clauses", [])
        data.setdefault("missing_clauses", [])
        data.setdefault("recommended_edits", [])
        data.setdefault("red_flags", [])

        clauses = data["clauses"]
        counts = {
            "clauses_reviewed": len(clauses),
            "red": sum(1 for c in clauses if (c.get("risk") or "").lower() == "red"),
            "yellow": sum(1 for c in clauses if (c.get("risk") or "").lower() == "yellow"),
            "green": sum(1 for c in clauses if (c.get("risk") or "").lower() == "green"),
            "missing": len(data["missing_clauses"]),
        }
        data["stats"] = counts

        await progress(
            "analyze",
            f"Reviewed {counts['clauses_reviewed']} clauses — "
            f"{counts['red']} high-risk, {counts['yellow']} to negotiate, "
            f"{counts['missing']} missing",
        )
        return data
