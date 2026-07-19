# Day 09 — AI Cybersecurity Audit Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Input a website URL or codebase. The agent runs automated security checks — detecting exposed API keys, weak authentication patterns, common OWASP vulnerabilities (XSS, SQLi, CSRF), insecure dependencies, and misconfigured headers — then produces a full security audit report with severity levels and fix recommendations.

## ✨ Key Features

- Two modes: live **URL scan** (HTTP security headers, HTTPS/TLS, cookies) or **code audit**
- OWASP Top 10 review (SQLi, XSS, CSRF, SSRF, path traversal, insecure crypto, etc.)
- Regex-based exposed-secret / API-key detection with automatic redaction
- Severity-rated findings (critical → info) with a letter grade & risk score
- Prioritized remediation roadmap with code-level fixes
- Downloadable PDF audit report

## 🛠️ Tech Stack

Python · OpenAI GPT-4o-mini · httpx · FastAPI · WebSockets · ReportLab · HTML · Tailwind CSS · Chart.js · JavaScript

> **Authorized use only** — scan systems and code you own or have explicit permission to test. Deterministic checks (headers, secret regexes) run locally; the OWASP analysis is done by the model.

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-09-ai-cybersecurity-audit
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example .env       # add your API keys
uvicorn main:app --reload
```

## 📌 Status

✅ Complete

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
