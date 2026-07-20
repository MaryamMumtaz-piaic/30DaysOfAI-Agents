# Day 12 — AI DevOps & CI/CD Intelligence Pipeline

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Paste a code diff or a GitHub PR URL and a multi-agent pipeline reviews it. Four specialists run **in parallel** — **Code Quality Agent** (readability, complexity), **Security Scanner** (OWASP, secrets, injection), **Test Coverage Agent** (coverage gaps), and **Performance Agent** (algorithmic/resource analysis). A fifth **Deployment Decision Agent** then merges their findings into an APPROVE / REQUEST CHANGES / BLOCK verdict with a deployment risk level, rollback plan, and a ready-to-post PR comment. Progress streams live over a WebSocket and the full report exports to PDF.

## ✨ Key Features

- Four analyst agents run concurrently (`asyncio.gather`), synthesized by a decision agent
- Pull diffs straight from a public GitHub PR URL (or paste your own)
- Live pipeline view — each agent lights up as it runs
- Per-agent 0-100 scores on a radar chart + findings-by-severity chart
- Security findings tagged with CWE / OWASP categories
- Deployment risk + rollback plan + copy-ready PR comment
- One-click PDF export of the full analysis

## 🛠️ Tech Stack

Python · OpenAI SDK · GitHub REST API · FastAPI · WebSockets · HTML · Tailwind CSS · Chart.js · ReportLab

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-12-ai-devops-pipeline
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
