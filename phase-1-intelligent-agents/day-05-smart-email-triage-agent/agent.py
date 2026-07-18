"""Smart email triage & auto-response agent.

Given a batch of unread emails (from a connected inbox, pasted, or the demo
sample set), the agent processes each email concurrently and produces:
  1. A category (urgent / important / normal / promotional / spam).
  2. A 0-100 priority score and an action-required flag.
  3. A one-line summary and extracted intent.
  4. A drafted, personalized reply that matches the sender's tone.

Progress is reported through an async callback so the FastAPI layer can
stream it to the browser over a WebSocket.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Awaitable, Callable

from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MAX_BODY_CHARS = 4000

ProgressFn = Callable[[str, str], Awaitable[None]]

VALID_CATEGORIES = {"urgent", "important", "normal", "promotional", "spam"}


async def _noop(stage: str, message: str) -> None:
    return None


class EmailTriageAgent:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def triage(
        self,
        emails: list[dict],
        user_name: str = "",
        progress: ProgressFn = _noop,
    ) -> dict:
        emails = [e for e in emails if (e.get("subject") or e.get("body"))]
        if not emails:
            raise ValueError("No emails provided to triage")

        await progress("start", f"Triaging {len(emails)} email(s)")

        # Process each email concurrently but report progress as they land.
        done = 0
        lock = asyncio.Lock()
        results: list[dict | None] = [None] * len(emails)

        async def _one(idx: int, email: dict) -> None:
            nonlocal done
            r = await self._classify(email, user_name)
            r["id"] = email.get("id", idx)
            r["from"] = email.get("from", "")
            r["subject"] = email.get("subject", "")
            r["received"] = email.get("received", "")
            results[idx] = r
            async with lock:
                done += 1
                await progress(
                    "triage",
                    f"[{done}/{len(emails)}] {r['category'].upper()} · "
                    f"{r['subject'][:48] or '(no subject)'}",
                )

        await asyncio.gather(*[_one(i, e) for i, e in enumerate(emails)])

        triaged = [r for r in results if r]
        triaged.sort(key=lambda r: r.get("priority", 0), reverse=True)

        stats = self._summarize(triaged)
        await progress(
            "done",
            f"Done — {stats['action_required']} need action, "
            f"{stats['by_category'].get('spam', 0)} spam",
        )
        return {"emails": triaged, "stats": stats}

    async def _classify(self, email: dict, user_name: str) -> dict:
        subject = (email.get("subject") or "").strip()
        sender = (email.get("from") or "").strip()
        body = (email.get("body") or "").strip()[:MAX_BODY_CHARS]

        sig = f"Sign the reply as {user_name}." if user_name else ""
        prompt = (
            "You are an executive assistant triaging an inbox. Analyze the single "
            "email below and return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "category": "urgent|important|normal|promotional|spam",\n'
            '  "priority": 0-100,\n'
            '  "action_required": true,\n'
            '  "sentiment": "positive|neutral|negative",\n'
            '  "intent": "3-6 word description of what the sender wants",\n'
            '  "summary": "one-sentence summary of the email",\n'
            '  "suggested_labels": ["short", "labels"],\n'
            '  "reply_needed": true,\n'
            '  "draft_reply": "a complete, personalized, professional reply that matches the sender\'s tone; empty string if no reply is needed (e.g. spam/promotional)"\n'
            "}\n"
            "Rules: 'urgent' = time-sensitive and needs a fast human response; "
            "'important' = matters but not time-critical; 'promotional' = marketing/newsletters; "
            "'spam' = unsolicited/scam/phishing. Higher priority = handle sooner. "
            "Only write draft_reply when reply_needed is true. Keep the reply concise and ready to send. "
            f"{sig}\n\n"
            f"From: {sender}\nSubject: {subject}\n\nBody:\n{body}"
        )

        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        data = json.loads(resp.choices[0].message.content)

        category = str(data.get("category", "normal")).lower()
        if category not in VALID_CATEGORIES:
            category = "normal"
        data["category"] = category
        data["priority"] = max(0, min(100, int(data.get("priority") or 0)))
        data.setdefault("action_required", False)
        data.setdefault("sentiment", "neutral")
        data.setdefault("intent", "")
        data.setdefault("summary", "")
        data.setdefault("suggested_labels", [])
        data.setdefault("reply_needed", False)
        data.setdefault("draft_reply", "")
        if not data["reply_needed"]:
            data["draft_reply"] = data.get("draft_reply") or ""
        return data

    def _summarize(self, triaged: list[dict]) -> dict:
        by_category: dict[str, int] = {}
        for r in triaged:
            by_category[r["category"]] = by_category.get(r["category"], 0) + 1
        return {
            "total": len(triaged),
            "action_required": sum(1 for r in triaged if r.get("action_required")),
            "replies_drafted": sum(1 for r in triaged if r.get("draft_reply")),
            "by_category": by_category,
        }
