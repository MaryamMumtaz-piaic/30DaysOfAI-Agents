# Day 02 — AI Code Debugger & Optimizer Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Paste any broken code (Python, JavaScript, TypeScript, etc.) and this agent detects all bugs, explains each error with root cause analysis, rewrites the fixed code, calculates Big-O complexity, and suggests performance optimizations. Full VS-Code-inspired web editor UI with syntax highlighting and diff view.

## ✨ Key Features

- Multi-language support (Python, JS, TS, Java, C++)
- Root-cause bug analysis with fix explanations
- Before/after code diff viewer
- Big-O complexity analysis
- Security vulnerability scanning (SQL injection, XSS, etc.)

## 🛠️ Tech Stack

Python · OpenAI GPT-4o · FastAPI · HTML · Tailwind CSS · JavaScript · CodeMirror · Diff2Html

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-02-ai-code-debugger-agent
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
