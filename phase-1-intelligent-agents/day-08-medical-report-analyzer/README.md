# Day 08 — AI Medical Report Analyzer

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Upload lab results, blood reports, or medical scans (PDF/image). The agent analyzes every value against healthy reference ranges, flags abnormal readings, explains what each marker means in plain English, identifies potential health risks, and generates a patient-friendly summary report with recommended next steps.

## ✨ Key Features

- PDF text extraction + image reading via GPT-4o vision (no Tesseract needed)
- Value-by-value comparison against medical reference ranges
- Risk flagging (normal / borderline / critical) with color coding & ↑↓ direction
- Plain-English explanation for every marker
- Potential-risk detection and recommended next steps / referrals
- Urgent-care banner for clearly out-of-range results
- Downloadable patient-friendly PDF summary

## 🛠️ Tech Stack

Python · OpenAI GPT-4o (vision) · pypdf · FastAPI · WebSockets · ReportLab · HTML · Tailwind CSS · Chart.js · JavaScript

> **Not a medical diagnosis** — this is an educational tool. Image uploads use the vision model directly, so no OCR install is required. Use a vision-capable `OPENAI_MODEL` (e.g. `gpt-4o` or `gpt-4o-mini`) for photos.

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-08-medical-report-analyzer
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
