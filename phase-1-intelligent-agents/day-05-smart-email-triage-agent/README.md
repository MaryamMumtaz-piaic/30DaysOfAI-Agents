# Day 05 — Smart Email Triage & Auto-Response Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Connect your Gmail inbox. The agent reads all unread emails, categorizes them by urgency and type, drafts personalized professional responses for each, detects spam, flags action-required emails, and maintains a clean priority inbox. Full dashboard with approve/edit/send workflow.

## ✨ Key Features

- Gmail API integration with OAuth2
- Automatic email categorization (urgent/normal/spam)
- AI-drafted personalized replies with tone matching
- One-click approve and send
- Thread context understanding and follow-up tracking

## 🛠️ Tech Stack

Python · OpenAI SDK · Gmail API · FastAPI · HTML · Tailwind CSS · JavaScript · OAuth2

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

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
