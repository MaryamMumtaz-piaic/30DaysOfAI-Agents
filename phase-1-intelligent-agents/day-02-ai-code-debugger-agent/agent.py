"""AI code debugger & optimizer agent.

Takes a code snippet + language, and returns a structured analysis:
  - bugs with root-cause explanations and severity
  - the fully fixed/rewritten code
  - Big-O time & space complexity (before and after)
  - security vulnerabilities (SQLi, XSS, etc.)
  - performance optimization suggestions
"""

from __future__ import annotations

import json
import os

from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "You are a senior software engineer and code auditor. Analyze the user's code "
    "rigorously and return ONLY JSON matching this exact schema:\n"
    "{\n"
    '  "language": "detected language",\n'
    '  "summary": "1-2 sentence overall assessment",\n'
    '  "bugs": [\n'
    '    {"title": "short name", "severity": "critical|high|medium|low",\n'
    '     "line": "line number or range or null",\n'
    '     "root_cause": "why it happens", "fix": "how it is fixed"}\n'
    "  ],\n"
    '  "fixed_code": "the complete corrected code as a single string",\n'
    '  "complexity": {"before_time": "O(...)", "before_space": "O(...)",\n'
    '                 "after_time": "O(...)", "after_space": "O(...)",\n'
    '                 "explanation": "brief reasoning"},\n'
    '  "security": [\n'
    '    {"title": "vuln name", "severity": "critical|high|medium|low",\n'
    '     "detail": "what and where", "remediation": "how to fix"}\n'
    "  ],\n"
    '  "optimizations": ["actionable performance/readability suggestion", "..."]\n'
    "}\n"
    "If the code has no bugs or no security issues, return empty arrays. "
    "Preserve the original language in fixed_code. Be precise and concise."
)


class CodeDebuggerAgent:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def analyze(self, code: str, language: str = "auto") -> dict:
        if not code.strip():
            raise ValueError("Code is empty")

        lang_hint = (
            "Auto-detect the language."
            if language in ("", "auto")
            else f"The language is {language}."
        )
        user_msg = f"{lang_hint}\n\nCode:\n```\n{code}\n```"

        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content)

        # Normalize so the UI can rely on every key existing.
        data.setdefault("language", language if language != "auto" else "unknown")
        data.setdefault("summary", "")
        data.setdefault("bugs", [])
        data.setdefault("fixed_code", code)
        data.setdefault(
            "complexity",
            {
                "before_time": "N/A", "before_space": "N/A",
                "after_time": "N/A", "after_space": "N/A", "explanation": "",
            },
        )
        data.setdefault("security", [])
        data.setdefault("optimizations", [])
        return data
