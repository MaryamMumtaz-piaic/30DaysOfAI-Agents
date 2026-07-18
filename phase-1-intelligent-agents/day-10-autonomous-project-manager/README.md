# Day 10 — Autonomous AI Project Manager

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Describe your project goal in one sentence. The agent autonomously breaks it into phases, generates detailed tasks with effort estimates, assigns team roles, builds a Gantt chart timeline, identifies dependencies and blockers, performs risk assessment, and delivers a complete project plan. Full interactive Kanban board UI with drag-and-drop.

## ✨ Key Features

- Autonomous task decomposition from a single goal input
- Effort estimation with ML-based story points
- Risk and blocker identification with mitigation strategies
- Auto-generated interactive Gantt chart
- Drag-and-drop Kanban board with sprint management

## 🛠️ Tech Stack

Python · OpenAI SDK · LangChain · FastAPI · HTML · Tailwind CSS · JavaScript · Frappe Gantt · SortableJS

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-10-autonomous-project-manager
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
