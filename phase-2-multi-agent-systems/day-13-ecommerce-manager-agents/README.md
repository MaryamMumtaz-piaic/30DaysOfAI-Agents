# Day 13 — Autonomous E-Commerce Operations Manager

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A fully autonomous e-commerce management system with 5 agents: **Inventory Monitor** (stock alerts + reorder logic), **Dynamic Pricing Agent** (competitor-based repricing), **Customer Review Analyst** (sentiment + response drafting), **Ad Copy Generator** (platform-specific creatives), and **Sales Forecaster** (demand prediction). Full admin dashboard with real-time metrics.

## ✨ Key Features

- Real-time inventory monitoring with auto-reorder triggers
- Dynamic pricing based on live competitor scraping
- Automated customer review sentiment responses
- Multi-platform ad copy generation (Google, Meta, Amazon)
- ML-based sales forecasting with trend analysis

## 🛠️ Tech Stack

Python · LangGraph · OpenAI SDK · FastAPI · HTML · Tailwind CSS · Chart.js · JavaScript · SQLite

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

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
