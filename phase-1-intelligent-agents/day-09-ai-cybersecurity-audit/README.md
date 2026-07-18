# Day 09 — AI Cybersecurity Audit Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Input a website URL or codebase. The agent runs automated security checks — detecting exposed API keys, weak authentication patterns, common OWASP vulnerabilities (XSS, SQLi, CSRF), insecure dependencies, and misconfigured headers — then produces a full security audit report with severity levels and fix recommendations.

## ✨ Key Features

- OWASP Top 10 vulnerability scanning
- Exposed secrets and API key detection
- Dependency vulnerability check against CVE database
- HTTP security header analysis
- Prioritized remediation roadmap with code-level fixes

## 🛠️ Tech Stack

Python · OpenAI SDK · Requests · BeautifulSoup · Safety · FastAPI · HTML · Tailwind CSS · JavaScript

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

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
