# Day 11 — AI Startup Validator Crew

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A 6-agent startup validation crew. Enter your startup idea and receive a complete venture-capital-style diligence packet. The agents run in sequence, each building on the prior one's output: **Market Researcher** (TAM/SAM/SOM), **Competitor Scout** (existing solutions), **Financial Modeler** (3-year projection), **Risk Analyst** (PESTLE), **Pitch Writer** (investor pitch + deck outline), and **Go/No-Go Scorer** (weighted 0-100 verdict). Progress streams live over a WebSocket, and the full report exports to PDF.

## ✨ Key Features

- 6 specialized agents with distinct expert roles, chained so context compounds
- Live crew progress streamed over WebSocket (each agent lights up as it runs)
- TAM / SAM / SOM market sizing with a bar chart
- 3-year revenue / cost / profit projection with a combo chart
- PESTLE risk framework with severity-scored mitigations
- Investor-ready elevator pitch and deck outline
- Weighted go / no-go verdict with a scorecard and rationale
- One-click investor-ready PDF export

## 🛠️ Tech Stack

Python · OpenAI SDK · FastAPI · WebSockets · HTML · Tailwind CSS · Chart.js · ReportLab

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-11-startup-validator-crew
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
