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
- Approve / edit / **regenerate** / send workflow per email
- **Real Gmail connection** via IMAP (read unread) + SMTP (send replies)
- Category-breakdown and priority charts + downloadable PDF report
- Built-in demo inbox (no Gmail login required) plus manual paste-in

## 🛠️ Tech Stack

Python · OpenAI GPT-4o-mini · FastAPI · WebSockets · IMAP/SMTP · ReportLab · HTML · Tailwind CSS · Chart.js · JavaScript

## 📧 Connect a real Gmail inbox

Click **Connect Gmail** in the UI and enter your address + a Gmail **App Password**
(not your normal password). Replies you approve are delivered for real via SMTP.

To create an App Password:

1. Turn on **2-Step Verification** at <https://myaccount.google.com/security>.
2. Open <https://myaccount.google.com/apppasswords>, name it (e.g. "Triage Agent"), and copy the 16-character code.
3. Paste your Gmail address and that code into the Connect dialog.

> Credentials are used only for the current session — they are sent to the local
> server to read/send your mail and are never written to disk. Prefer the sample
> inbox for a quick demo with just an OpenAI key.

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
