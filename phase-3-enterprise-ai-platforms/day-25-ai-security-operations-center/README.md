# Day 25 — AI Security Operations Center (SOC)

> **Phase 3 — Enterprise-Grade AI Platforms**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

An AI-powered cybersecurity monitoring platform. Continuously scans server logs, network traffic patterns, and user behavior anomalies. Agents detect threats, classify severity (P0-P4), trace attack chains using MITRE ATT&CK, generate incident reports, suggest remediation playbooks, and auto-block suspicious IPs via firewall API. Real-time threat map with global visualization.

## ✨ Key Features

- Real-time log and network traffic anomaly detection
- MITRE ATT&CK framework threat classification
- Full attack chain visualization and timeline reconstruction
- Automated remediation for common threat patterns
- Live global threat map powered by D3.js

## 🛠️ Tech Stack

Python · LangGraph · OpenAI SDK · FastAPI · HTML · Tailwind CSS · D3.js · JavaScript · WebSockets · PostgreSQL

## ⚙️ Setup

```bash
cd phase-3-enterprise-ai-platforms/day-25-ai-security-operations-center
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
