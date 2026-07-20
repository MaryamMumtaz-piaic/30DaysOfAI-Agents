"""AI DevOps & CI/CD Intelligence Pipeline.

Given a pull-request diff (pasted directly or fetched from a GitHub PR URL), five
specialist agents analyze it in parallel:

  1. Code Quality Agent   — readability, complexity, maintainability.
  2. Security Scanner      — OWASP-style issues, secrets, unsafe patterns.
  3. Test Coverage Agent   — missing tests and coverage gaps.
  4. Performance Agent     — algorithmic and resource concerns.

A sixth agent then merges their findings:

  5. Deployment Decision   — APPROVE / REQUEST CHANGES / BLOCK with reasoning,
                             a deployment risk level, and rollback advice.

Because the four analysts are independent they run concurrently with
asyncio.gather; the decision agent runs afterwards on their combined output.
Progress is streamed to the browser over a WebSocket through an async callback.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Awaitable, Callable

import httpx
from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_DIFF_CHARS = 24_000

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


class DevOpsPipeline:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)
        self.github_token = os.getenv("GITHUB_TOKEN", "").strip()

    async def analyze(
        self,
        diff: str = "",
        pr_url: str = "",
        title: str = "",
        progress: ProgressFn = _noop,
    ) -> dict:
        diff = (diff or "").strip()
        pr_url = (pr_url or "").strip()
        title = (title or "").strip()

        meta: dict = {}
        if not diff and pr_url:
            await progress("fetch", f"Fetching diff from {pr_url}")
            diff, meta = await self._fetch_pr(pr_url)

        diff = diff.strip()
        if len(diff) < 20:
            raise ValueError("Paste a code diff or provide a valid GitHub PR URL")

        truncated = len(diff) > MAX_DIFF_CHARS
        if truncated:
            diff = diff[:MAX_DIFF_CHARS]

        title = title or meta.get("title", "") or "Pull request"
        stats = _diff_stats(diff)
        await progress(
            "start",
            f"Analyzing {stats['files']} file(s) · +{stats['additions']}/-{stats['deletions']} lines",
        )

        await progress("quality", "Code Quality, Security, Coverage & Performance agents running")

        quality, security, coverage, performance = await asyncio.gather(
            self._quality(diff, title),
            self._security(diff, title),
            self._coverage(diff, title),
            self._performance(diff, title),
        )

        await progress("quality", "Code Quality Agent finished")
        await progress("security", f"Security Scanner found {len(security.get('findings', []))} issue(s)")
        await progress("coverage", "Test Coverage Agent finished")
        await progress("performance", "Performance Agent finished")

        analyses = {
            "quality": quality,
            "security": security,
            "coverage": coverage,
            "performance": performance,
        }

        await progress("deploy", "Deployment Decision Agent synthesizing verdict")
        decision = await self._decision(title, analyses)

        result = {
            "title": title,
            "pr_url": pr_url,
            "meta": meta,
            "diff_stats": {**stats, "truncated": truncated},
            "analyses": analyses,
            "decision": decision,
        }
        result = self._post_process(result)
        d = result["decision"]
        await progress("done", f"Decision: {d['decision']} · risk {d['risk']}")
        return result

    # ----- GitHub ------------------------------------------------------------

    async def _fetch_pr(self, pr_url: str) -> tuple[str, dict]:
        m = re.match(
            r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url.strip()
        )
        if not m:
            raise ValueError("Not a valid GitHub PR URL (…/owner/repo/pull/123)")
        owner, repo, number = m.group(1), m.group(2), m.group(3)
        api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"

        headers = {"Accept": "application/vnd.github+json", "User-Agent": "devops-pipeline"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        async with httpx.AsyncClient(timeout=30) as client:
            info = await client.get(api, headers=headers)
            if info.status_code == 404:
                raise ValueError("PR not found (private repo? set GITHUB_TOKEN)")
            info.raise_for_status()
            data = info.json()

            diff_resp = await client.get(
                api, headers={**headers, "Accept": "application/vnd.github.v3.diff"}
            )
            diff_resp.raise_for_status()

        meta = {
            "title": data.get("title", ""),
            "author": (data.get("user") or {}).get("login", ""),
            "base": (data.get("base") or {}).get("ref", ""),
            "head": (data.get("head") or {}).get("ref", ""),
            "changed_files": data.get("changed_files", 0),
        }
        return diff_resp.text, meta

    # ----- individual agents -------------------------------------------------

    async def _quality(self, diff: str, title: str) -> dict:
        prompt = (
            "You are a senior code reviewer focused on code quality and maintainability. Review the "
            "diff. Return ONLY JSON:\n"
            "{\n"
            '  "score": 0,\n'
            '  "summary": "1-2 sentence quality assessment",\n'
            '  "findings": [\n'
            '    {"severity": "low|medium|high", "title": "short title",\n'
            '     "detail": "what and why", "file": "path if known", "suggestion": "how to fix"}\n'
            "  ],\n"
            '  "positives": ["something done well"]\n'
            "}\n"
            "score is 0-100 (100 = excellent). Focus on readability, naming, complexity, duplication, "
            "error handling, and dead code. Only report real issues in the changed lines.\n\n"
            + _diff_block(diff, title)
        )
        return await self._json(prompt, 0.3)

    async def _security(self, diff: str, title: str) -> dict:
        prompt = (
            "You are an application security engineer. Scan the diff for vulnerabilities. Return ONLY "
            "JSON:\n"
            "{\n"
            '  "score": 0,\n'
            '  "summary": "1-2 sentence security assessment",\n'
            '  "findings": [\n'
            '    {"severity": "low|medium|high|critical", "title": "short title",\n'
            '     "detail": "the vulnerability and its impact", "file": "path if known",\n'
            '     "cwe": "CWE-XX or OWASP category if applicable", "suggestion": "remediation"}\n'
            "  ]\n"
            "}\n"
            "score is 0-100 (100 = no security concerns). Check for injection, hardcoded secrets/keys, "
            "unsafe deserialization, weak crypto, missing authz, XSS, SSRF, path traversal, and "
            "command injection. Report only issues evidenced by the diff.\n\n"
            + _diff_block(diff, title)
        )
        return await self._json(prompt, 0.2)

    async def _coverage(self, diff: str, title: str) -> dict:
        prompt = (
            "You are a test engineer. Assess whether the diff is adequately tested. Return ONLY JSON:\n"
            "{\n"
            '  "score": 0,\n'
            '  "summary": "1-2 sentence coverage assessment",\n'
            '  "adds_tests": true,\n'
            '  "gaps": [\n'
            '    {"area": "what is untested", "risk": "low|medium|high",\n'
            '     "suggestion": "the test(s) to add"}\n'
            "  ]\n"
            "}\n"
            "score is 0-100 (100 = well covered). adds_tests is whether the diff itself adds/updates "
            "tests. Flag new logic, branches, and edge cases that lack tests.\n\n"
            + _diff_block(diff, title)
        )
        return await self._json(prompt, 0.3)

    async def _performance(self, diff: str, title: str) -> dict:
        prompt = (
            "You are a performance engineer. Analyze the diff for performance concerns. Return ONLY "
            "JSON:\n"
            "{\n"
            '  "score": 0,\n'
            '  "summary": "1-2 sentence performance assessment",\n'
            '  "findings": [\n'
            '    {"severity": "low|medium|high", "title": "short title",\n'
            '     "detail": "the concern (e.g. N+1 query, O(n^2) loop, blocking I/O)",\n'
            '     "file": "path if known", "suggestion": "the optimization"}\n'
            "  ]\n"
            "}\n"
            "score is 0-100 (100 = no concerns). Check algorithmic complexity, N+1 queries, unbounded "
            "memory, blocking calls in hot paths, and unnecessary work in loops.\n\n"
            + _diff_block(diff, title)
        )
        return await self._json(prompt, 0.3)

    async def _decision(self, title: str, analyses: dict) -> dict:
        summary = {
            k: {
                "score": v.get("score"),
                "summary": v.get("summary"),
                "issues": (v.get("findings") or v.get("gaps") or []),
            }
            for k, v in analyses.items()
        }
        prompt = (
            "You are the deployment gatekeeper in a CI/CD pipeline. Given the four specialist reports "
            "below, make a merge/deploy decision. Return ONLY JSON:\n"
            "{\n"
            '  "decision": "APPROVE|REQUEST CHANGES|BLOCK",\n'
            '  "risk": "low|medium|high",\n'
            '  "confidence": 0,\n'
            '  "rationale": "3-4 sentence justification referencing the specialist findings",\n'
            '  "blocking_issues": ["issue that must be fixed before merge"],\n'
            '  "required_actions": ["action the author should take"],\n'
            '  "rollback_plan": "how to safely roll back if this deploy misbehaves",\n'
            '  "pr_comment": "a concise, friendly PR review comment (markdown) summarizing the decision"\n'
            "}\n"
            "confidence is 0-100. BLOCK for critical security issues; REQUEST CHANGES for material "
            "quality/coverage/performance gaps; APPROVE only when risk is acceptable.\n\n"
            f"PR TITLE: {title}\n"
            f"SPECIALIST REPORTS:\n{json.dumps(summary, indent=2)[:12000]}"
        )
        return await self._json(prompt, 0.3)

    # ----- helpers -----------------------------------------------------------

    async def _json(self, prompt: str, temperature: float) -> dict:
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return json.loads(resp.choices[0].message.content)

    def _post_process(self, r: dict) -> dict:
        analyses = r["analyses"]

        for key in ("quality", "security", "coverage", "performance"):
            a = analyses.setdefault(key, {})
            a["score"] = _clamp(a.get("score"))
            a.setdefault("summary", "")
            fk = "gaps" if key == "coverage" else "findings"
            clean = []
            for f in a.get(fk, []) or []:
                if not isinstance(f, dict):
                    continue
                sev = str(f.get("severity") or f.get("risk") or "medium").lower()
                f["severity"] = sev if sev in ("low", "medium", "high", "critical") else "medium"
                clean.append(f)
            a[fk] = clean
            if key != "coverage":
                a.setdefault("positives", a.get("positives", []))

        d = r["decision"]
        d["confidence"] = _clamp(d.get("confidence"))
        risk = str(d.get("risk", "medium")).lower()
        d["risk"] = risk if risk in ("low", "medium", "high") else "medium"
        dec = str(d.get("decision", "")).upper().strip()
        if dec not in ("APPROVE", "REQUEST CHANGES", "BLOCK"):
            dec = "REQUEST CHANGES"
        d["decision"] = dec
        d.setdefault("rationale", "")
        d.setdefault("blocking_issues", [])
        d.setdefault("required_actions", [])
        d.setdefault("rollback_plan", "")
        d.setdefault("pr_comment", "")

        scores = [analyses[k]["score"] for k in ("quality", "security", "coverage", "performance")]
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for key in ("quality", "security", "performance"):
            for f in analyses[key].get("findings", []):
                counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        for g in analyses["coverage"].get("gaps", []):
            counts[g["severity"]] = counts.get(g["severity"], 0) + 1

        r["stats"] = {
            "overall_score": round(sum(scores) / len(scores)) if scores else 0,
            "total_findings": sum(counts.values()),
            "by_severity": counts,
            "decision": d["decision"],
            "risk": d["risk"],
        }
        return r


# ----- module-level diff utilities -------------------------------------------

def _diff_block(diff: str, title: str) -> str:
    return f"PR TITLE: {title}\n\nUNIFIED DIFF:\n```diff\n{diff}\n```"


def _diff_stats(diff: str) -> dict:
    files: set[str] = set()
    additions = deletions = 0
    for line in diff.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            path = line[4:].strip()
            if path and path not in ("/dev/null",):
                files.add(re.sub(r"^[ab]/", "", path))
        elif line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 3:
                files.add(re.sub(r"^[ab]/", "", parts[2]))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return {"files": len(files), "additions": additions, "deletions": deletions}


def _clamp(v) -> int:
    try:
        return max(0, min(100, int(float(v))))
    except (TypeError, ValueError):
        return 0
