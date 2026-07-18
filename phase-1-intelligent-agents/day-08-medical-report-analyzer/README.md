# Day 08 — AI Medical Report Analyzer

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Upload lab results, blood reports, or medical scans (PDF/image). The agent analyzes every value against healthy reference ranges, flags abnormal readings, explains what each marker means in plain English, identifies potential health risks, and generates a patient-friendly summary report with recommended next steps.

## ✨ Key Features

- OCR-based report text extraction from PDFs and images
- Value-by-value comparison against medical reference ranges
- Risk flagging (normal/borderline/critical) with color coding
- Plain-English explanations for medical terminology
- Recommended follow-up actions and specialist referrals

## 🛠️ Tech Stack

Python · OpenAI GPT-4o Vision · Tesseract OCR · FastAPI · HTML · Tailwind CSS · JavaScript · PyPDF2

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

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
