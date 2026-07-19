# Day 10 — Autonomous AI Project Manager

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Describe your project goal in one sentence. The agent autonomously breaks it into phases, generates detailed tasks with effort estimates, assigns team roles, builds a Gantt chart timeline, identifies dependencies and blockers, performs risk assessment, and delivers a complete project plan. Full interactive Kanban board UI with drag-and-drop.

## ✨ Key Features

- Autonomous task decomposition from a single-sentence goal
- Effort estimation (Fibonacci story points + day estimates) and role assignment
- Dependency mapping with critical-path highlighting
- Auto-generated Gantt timeline and effort-by-phase chart
- Drag-and-drop Kanban board (To Do / In Progress / Done)
- Risk assessment with likelihood, impact, and mitigations
- Downloadable PDF project plan

## 🛠️ Tech Stack

Python · OpenAI GPT-4o-mini · FastAPI · WebSockets · ReportLab · HTML · Tailwind CSS · Chart.js · native drag-and-drop · JavaScript

> Configure team size and an optional deadline; the agent schedules task start-offsets so work parallelizes across the team.

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

✅ Complete

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
