"""AI cybersecurity audit agent (defensive).

Two scan modes:
  - URL:  fetches the site, evaluates HTTPS/security headers/cookies, then asks
          OpenAI to interpret the posture and suggest hardening.
  - Code: regex-scans for exposed secrets, then asks OpenAI to review the code
          for OWASP Top 10 issues (XSS, SQLi, CSRF, insecure deserialization, etc.)
          with code-level fixes.

Deterministic findings (scanner.py) are merged with the LLM findings, then the
agent computes a risk score and severity breakdown.

Progress is reported through an async callback so the FastAPI layer can stream
it to the browser over a WebSocket.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Awaitable, Callable

from openai import AsyncOpenAI

import scanner

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MAX_CODE_CHARS = 18000

ProgressFn = Callable[[str, str], Awaitable[None]]

SEVERITY_WEIGHT = {"critical": 40, "high": 20, "medium": 8, "low": 3, "info": 1}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


async def _noop(stage: str, message: str) -> None:
    return None


class SecurityAuditAgent:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def audit(
        self,
        mode: str,
        target: str,
        language: str = "",
        progress: ProgressFn = _noop,
    ) -> dict:
        mode = (mode or "url").lower()
        if mode == "url":
            return await self._audit_url(target, progress)
        if mode == "code":
            return await self._audit_code(target, language, progress)
        raise ValueError("mode must be 'url' or 'code'")

    # ------------------------------------------------------------------ URL

    async def _audit_url(self, target: str, progress: ProgressFn) -> dict:
        url = scanner.normalize_url(target)
        if not url:
            raise ValueError("No URL provided")

        await progress("start", f"Scanning {url}")
        await progress("fetch", "Fetching site and inspecting HTTP security headers")
        scan = await asyncio.to_thread(scanner.scan_headers, url)
        await progress(
            "fetch",
            f"HTTP {scan['status']} · HTTPS: {'yes' if scan['https'] else 'no'} · "
            f"{len(scan['findings'])} header/transport findings",
        )

        await progress("analyze", "Asking the model to interpret the security posture")
        present = scan["present"]
        llm = await self._llm_url(url, scan)
        findings = scan["findings"] + llm.get("findings", [])

        result = self._finalize(
            target=url,
            mode="url",
            findings=findings,
            summary=llm.get("summary", ""),
            recommendations=llm.get("recommendations", []),
            extra={"headers_present": present, "final_url": scan["final_url"],
                   "status": scan["status"], "https": scan["https"]},
        )
        await progress("done", f"Audit complete — risk score {result['risk_score']}/100")
        return result

    async def _llm_url(self, url: str, scan: dict) -> dict:
        prompt = (
            "You are a web security auditor performing an AUTHORIZED defensive review. "
            "Given the HTTP scan results below, add any additional posture findings NOT "
            "already covered (e.g. mixed content risk, caching of sensitive data, weak TLS "
            "expectations) and write an overall assessment. Do NOT repeat the header findings "
            "already listed. Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "summary": "2-3 sentence overall security posture assessment",\n'
            '  "findings": [\n'
            '    {"title": "concise issue", "severity": "critical|high|medium|low|info",\n'
            '     "category": "e.g. TLS, Configuration, Privacy", "detail": "why it matters",\n'
            '     "fix": "concrete remediation"}\n'
            "  ],\n"
            '  "recommendations": ["prioritized hardening step"]\n'
            "}\n\n"
            f"URL: {url}\n"
            f"Scan JSON: {json.dumps({k: scan[k] for k in ('status','https','final_url','present','findings')})}"
        )
        return await self._json(prompt)

    # ----------------------------------------------------------------- Code

    async def _audit_code(self, code: str, language: str, progress: ProgressFn) -> dict:
        code = (code or "").strip()
        if len(code) < 20:
            raise ValueError("Code is too short to audit")
        truncated = len(code) > MAX_CODE_CHARS
        code = code[:MAX_CODE_CHARS]

        await progress("start", f"Auditing {len(code):,} characters of code")
        if truncated:
            await progress("start", f"Code is long — auditing the first {MAX_CODE_CHARS:,} characters")

        await progress("secrets", "Scanning for exposed secrets and API keys")
        secret_findings = scanner.scan_secrets(code)
        await progress("secrets", f"Found {len(secret_findings)} potential secret(s)")

        await progress("analyze", "Reviewing code for OWASP Top 10 vulnerabilities")
        llm = await self._llm_code(code, language)
        findings = secret_findings + llm.get("findings", [])

        result = self._finalize(
            target=f"{language or 'code'} snippet",
            mode="code",
            findings=findings,
            summary=llm.get("summary", ""),
            recommendations=llm.get("recommendations", []),
            extra={"truncated": truncated, "language": language},
        )
        await progress("done", f"Audit complete — risk score {result['risk_score']}/100")
        return result

    async def _llm_code(self, code: str, language: str) -> dict:
        lang = f"The code is written in {language}." if language else ""
        prompt = (
            "You are a secure-code reviewer performing an AUTHORIZED audit. Review the code "
            "for OWASP Top 10 and common vulnerabilities: injection (SQLi, command, LDAP), "
            "XSS, CSRF, insecure deserialization, broken authentication/authorization, "
            "path traversal, SSRF, insecure crypto, hardcoded credentials, unsafe eval, and "
            "missing input validation. Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "summary": "2-3 sentence overall assessment of the code\'s security",\n'
            '  "findings": [\n'
            "    {\n"
            '      "title": "concise vulnerability name",\n'
            '      "severity": "critical|high|medium|low|info",\n'
            '      "category": "e.g. Injection, XSS, Auth, Crypto",\n'
            '      "cwe": "CWE-XX if applicable, else empty",\n'
            '      "line": 0,\n'
            '      "detail": "what the vulnerability is and how it could be exploited",\n'
            '      "fix": "specific code-level remediation",\n'
            '      "fix_code": "a short corrected code snippet, or empty string"\n'
            "    }\n"
            "  ],\n"
            '  "recommendations": ["prioritized remediation step"]\n'
            "}\n"
            "Only report real issues; do not invent vulnerabilities. Use line numbers from the "
            "code as given (1-indexed).\n"
            f"{lang}\n\n--- CODE ---\n{_number_lines(code)}"
        )
        return await self._json(prompt)

    # ------------------------------------------------------------- helpers

    async def _json(self, prompt: str) -> dict:
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        try:
            d = json.loads(resp.choices[0].message.content)
        except (json.JSONDecodeError, TypeError):
            d = {}
        if not isinstance(d, dict):
            d = {}
        d.setdefault("summary", "")
        d.setdefault("findings", [])
        d.setdefault("recommendations", [])
        return d

    def _finalize(
        self, target: str, mode: str, findings: list[dict],
        summary: str, recommendations: list[dict], extra: dict,
    ) -> dict:
        clean: list[dict] = []
        for f in findings:
            if not isinstance(f, dict) or not f.get("title"):
                continue
            sev = str(f.get("severity", "info")).lower()
            if sev not in SEVERITY_WEIGHT:
                sev = "info"
            f["severity"] = sev
            f.setdefault("category", "General")
            f.setdefault("detail", "")
            f.setdefault("fix", "")
            clean.append(f)

        clean.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 5))

        counts = {s: sum(1 for f in clean if f["severity"] == s)
                  for s in ("critical", "high", "medium", "low", "info")}

        raw = sum(SEVERITY_WEIGHT[f["severity"]] for f in clean)
        risk_score = min(100, raw)
        grade = _grade(risk_score, counts)

        return {
            "target": target,
            "mode": mode,
            "summary": summary,
            "risk_score": risk_score,
            "grade": grade,
            "counts": counts,
            "total": len(clean),
            "findings": clean,
            "recommendations": recommendations,
            **extra,
        }


def _number_lines(code: str) -> str:
    return "\n".join(f"{i}: {ln}" for i, ln in enumerate(code.splitlines(), 1))


def _grade(score: int, counts: dict) -> str:
    if counts["critical"]:
        return "F"
    if score >= 60:
        return "D"
    if score >= 35:
        return "C"
    if score >= 15:
        return "B"
    return "A"
