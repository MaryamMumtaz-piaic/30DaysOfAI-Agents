# Day 26 — Enterprise AI Workflow Automation Platform

> **Phase 3 — Enterprise-Grade AI Platforms**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A visual drag-and-drop AI workflow builder — think n8n but AI-native. Users build agent pipelines visually: choose from 20+ agent node types, connect them with conditional logic, configure triggers (webhook, cron, email, API), and deploy with one click. Real-time execution monitoring and a built-in marketplace for sharing pre-built workflows.

## ✨ Key Features

- Visual node-based workflow builder with Canvas API
- 20+ pre-built agent node types (researcher, writer, coder, analyzer)
- Conditional branching and loop logic in workflows
- Webhook, cron, and event-based trigger system
- Community marketplace for discovering and sharing workflows

## 🛠️ Tech Stack

Python · LangGraph · CrewAI · FastAPI · HTML · Tailwind CSS · JavaScript · Canvas API · PostgreSQL · Redis · Docker

## ⚙️ Setup

```bash
cd phase-3-enterprise-ai-platforms/day-26-enterprise-workflow-automation
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example .env       # add your API keys
docker compose up --build
```

## 📌 Status

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
