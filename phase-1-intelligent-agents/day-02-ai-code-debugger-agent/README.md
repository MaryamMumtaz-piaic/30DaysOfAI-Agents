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

## 🗂️ Project Structure

```
day-02-ai-code-debugger-agent/
├── main.py            # FastAPI app: web UI + /api/analyze endpoint
├── agent.py           # OpenAI-based code analysis (bugs, Big-O, security)
├── requirements.txt
├── .env.example
└── static/
    └── index.html     # CodeMirror editor UI (light theme, navbar/footer)
```

## 🔬 How It Works

1. Paste code into the CodeMirror editor and pick a language (or auto-detect)
2. The agent sends it to OpenAI with a strict JSON schema prompt
3. Returns structured results: **bugs** (with root cause + fix), **fixed code**,
   **Big-O complexity** (before/after), **security vulnerabilities**, and
   **optimization suggestions**
4. The UI renders everything with severity color-coding and a copy-to-clipboard fixed-code block

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-02-ai-code-debugger-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # add your OPENAI_API_KEY
uvicorn main:app --reload
```

Then open **http://localhost:8000** and paste code (or click "Load sample").

## 🔑 Required API Key

| Key | Where to get it |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |

## 📌 Status

✅ Functional — bug detection, fixed code, Big-O, and security scan working

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
