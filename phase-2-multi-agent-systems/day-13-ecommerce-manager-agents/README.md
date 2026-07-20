# Day 13 — Autonomous E-Commerce Operations Manager

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Enter your product catalog (stock, price, cost, competitor price, weekly sales, reviews) and five agents run the store: **Inventory Monitor** (stock health + reorder quantities), **Dynamic Pricing Agent** (competitor-aware, margin-protecting repricing), **Sales Forecaster** (trend-based demand + revenue projection), **Customer Review Analyst** (sentiment + drafted replies), and **Ad Copy Generator** (Google/Meta/Amazon creatives). The three numeric agents run deterministically for reproducible figures; the two language agents run concurrently. Progress streams live over a WebSocket and the full dashboard exports to PDF.

## ✨ Key Features

- Editable catalog dashboard — no database setup required
- Inventory monitoring with status tiers and auto-computed reorder quantities
- Dynamic pricing with a margin floor and competitor undercut logic
- Trend-aware sales forecast with per-product revenue projection
- AI review sentiment analysis with ready-to-post reply drafts
- Multi-platform ad copy (Google, Meta, Amazon)
- Live agent progress and one-click PDF operations report

## 🛠️ Tech Stack

Python · OpenAI SDK · FastAPI · WebSockets · HTML · Tailwind CSS · Chart.js · ReportLab

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-13-ecommerce-manager-agents
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
