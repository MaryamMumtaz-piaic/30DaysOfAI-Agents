# Day 12 — AI DevOps & CI/CD Intelligence Pipeline

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Connect your GitHub repo. A multi-agent system analyzes every pull request: **Code Quality Agent** (linting, complexity), **Security Scanner Agent** (OWASP, secrets), **Test Coverage Agent** (coverage gaps), **Performance Agent** (algorithmic analysis), and **Deployment Decision Agent** (approve/reject with reasoning). Live GitHub webhook integration with automated PR comments.

## ✨ Key Features

- GitHub webhook integration for real PR events
- Parallel multi-agent analysis with merged final report
- Automated approve/request-changes PR comments
- Security and performance scoring per commit
- Deployment risk assessment with rollback advice

## 🛠️ Tech Stack

Python · CrewAI · GitHub API · FastAPI · HTML · Tailwind CSS · JavaScript · WebSockets · Docker

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

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
