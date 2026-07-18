# Day 14 — AI Real Estate Investment Analyzer

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A 5-agent real estate intelligence system. Input a property address and budget. Agents perform: **Market Valuation** (comparables, price/sqft trends), **Rental Income Projection** (Airbnb vs long-term), **Neighborhood Analysis** (crime, schools, amenities scoring), **ROI Calculator** (cap rate, cash-on-cash return), **Investment Report Writer**. Interactive property map dashboard.

## ✨ Key Features

- Real estate comparable data scraping
- Dual rental model (short-term vs long-term) comparison
- Neighborhood scoring across 8 dimensions
- Full ROI, cap rate, and cash flow calculation
- Interactive Leaflet.js property map with heatmaps

## 🛠️ Tech Stack

Python · CrewAI · OpenAI SDK · FastAPI · HTML · Tailwind CSS · Leaflet.js · Chart.js · JavaScript

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-14-real-estate-ai-system
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
