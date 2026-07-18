# Day 22 — AI-Powered CRM with Sales Intelligence

> **Phase 3 — Enterprise-Grade AI Platforms**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A full AI-native CRM. Manage leads, contacts, and deals. The AI agent analyzes every interaction, scores leads automatically, predicts deal close probability, drafts follow-up emails, transcribes sales calls (Whisper), identifies objection patterns, and generates coaching tips per sales rep. Full pipeline kanban with revenue analytics.

## ✨ Key Features

- AI lead scoring from behavioral and interaction signals
- Deal close probability prediction with confidence interval
- Sales call transcription and keyword extraction via Whisper
- Automated follow-up email drafting with personalization
- Sales rep performance coaching and objection handling tips

## 🛠️ Tech Stack

Python · OpenAI GPT-4o + Whisper · FastAPI · HTML · Tailwind CSS · JavaScript · SQLite · Chart.js

## ⚙️ Setup

```bash
cd phase-3-enterprise-ai-platforms/day-22-ai-powered-crm
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
