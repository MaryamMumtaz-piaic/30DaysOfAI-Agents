# Day 05 — Smart Email Triage & Auto-Response Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Connect your Gmail inbox. The agent reads all unread emails, categorizes them by urgency and type, drafts personalized professional responses for each, detects spam, flags action-required emails, and maintains a clean priority inbox. Full dashboard with approve/edit/send workflow.

## ✨ Key Features

- Automatic categorization (urgent / important / normal / promotional / spam)
- Spam & phishing detection
- Priority scoring (0–100) with action-required flags
- AI-drafted personalized replies with tone matching
- Approve / edit / send workflow per email
- Category-breakdown and priority charts + downloadable PDF report
- Built-in demo inbox (no Gmail OAuth required) plus manual paste-in

## 🛠️ Tech Stack

Python · OpenAI GPT-4o-mini · FastAPI · WebSockets · ReportLab · HTML · Tailwind CSS · Chart.js · JavaScript

> Ships with a sample inbox so you can try it with only an OpenAI key. Swap `sample_inbox.py` / the `/send` route for the Gmail API + OAuth2 to run against a real mailbox.

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-05-smart-email-triage-agent
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
