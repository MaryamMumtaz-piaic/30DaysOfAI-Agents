# Day 17 — AI Supply Chain Risk & Optimizer

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A supply chain intelligence platform with 5 agents. Input your product BOM (Bill of Materials) and supplier list. Agents perform: **Supplier Risk Assessment** (geopolitical, financial stability), **Lead Time Optimizer** (optimal routing logic), **Cost Reduction Analyst** (alternative sourcing opportunities), **Demand Forecaster** (seasonal trend modeling), **Disruption Alert Agent** (real-time news-based risk detection). Full logistics network dashboard.

## ✨ Key Features

- Multi-dimensional supplier risk scoring
- Optimal sourcing route calculation with cost modeling
- Demand forecasting with seasonal adjustments
- Real-time global disruption alerts from news APIs
- Interactive D3.js supply chain network visualization

## 🛠️ Tech Stack

Python · LangGraph · OpenAI SDK · NewsAPI · FastAPI · HTML · Tailwind CSS · D3.js · JavaScript

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-17-supply-chain-optimizer
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
