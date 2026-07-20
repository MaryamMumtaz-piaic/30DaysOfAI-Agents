# Day 14 — AI Real Estate Investment Analyzer

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Enter a property address, budget, and details, and five agents evaluate the deal: **Market Valuation** (estimated value, price/sqft, comparables, trend), **Rental Projection** (long-term vs short-term/Airbnb monthly income), **Neighborhood Analysis** (8-dimension livability scoring), **ROI Calculator** (cap rate, cash-on-cash return, monthly cash flow), and **Investment Report Writer** (verdict + thesis). The three analytical agents run concurrently, the ROI figures are computed deterministically in Python, and the address is geocoded so the dashboard drops a live map pin. Progress streams over a WebSocket and the full report exports to PDF.

## ✨ Key Features

- Three analytical agents run concurrently, then a deterministic ROI engine + report writer
- Dual rental model (short-term vs long-term) comparison with a recommendation
- Neighborhood scoring across 8 dimensions on a radar chart
- Full ROI: cap rate, cash-on-cash, NOI, and monthly cash-flow waterfall
- Standard financing assumptions (25% down, 7%/30yr, vacancy/mgmt/maintenance reserves)
- Interactive Leaflet.js property map (OpenStreetMap geocoding)
- Investment verdict (STRONG BUY / BUY / HOLD / PASS) with one-click PDF export

## 🛠️ Tech Stack

Python · OpenAI SDK · FastAPI · WebSockets · OpenStreetMap (Nominatim) · HTML · Tailwind CSS · Leaflet.js · Chart.js · ReportLab

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

✅ Complete

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
