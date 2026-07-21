"""AI Legal Contract Generation & Review System — Day 16

4-Agent Pipeline:
  1. Contract Drafter    — Generates jurisdiction-aware, professional contract language
  2. Risk Reviewer       — Scores each clause 1-10 for legal risk with explanations
  3. Negotiation Advisor — Suggests strategic compromise language per risky clause
  4. Plain Language Translator — Rewrites the contract in jargon-free English

Architecture: FastAPI + WebSocket streaming + OpenAI GPT-4o-mini + ReportLab PDF export
"""

from __future__ import annotations

import json
import os
import re
import asyncio
from typing import Awaitable, Callable, Any

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


# ---------------------------------------------------------------------------
# Contract templates for pre-filling form fields
# ---------------------------------------------------------------------------

CONTRACT_TEMPLATES: dict[str, dict] = {
    "nda": {
        "name": "Non-Disclosure Agreement (NDA)",
        "fields": {
            "party_a": "Acme Corp",
            "party_b": "Beta Solutions",
            "jurisdiction": "New York, USA",
            "duration": "2 years",
            "purpose": "Evaluation of potential business partnership",
        },
    },
    "sla": {
        "name": "Service Level Agreement (SLA)",
        "fields": {
            "party_a": "TechService Inc.",
            "party_b": "Enterprise Client Ltd.",
            "jurisdiction": "California, USA",
            "duration": "1 year",
            "purpose": "24/7 cloud infrastructure management with 99.9% uptime guarantee",
        },
    },
    "employment": {
        "name": "Employment Contract",
        "fields": {
            "party_a": "Innovatech LLC",
            "party_b": "Jane Smith",
            "jurisdiction": "Texas, USA",
            "duration": "Indefinite (at-will)",
            "purpose": "Full-time Senior Software Engineer position",
        },
    },
    "vendor": {
        "name": "Vendor Agreement",
        "fields": {
            "party_a": "GlobalRetail Corp",
            "party_b": "Supply Masters Ltd.",
            "jurisdiction": "Delaware, USA",
            "duration": "3 years",
            "purpose": "Supply of electronic components and hardware",
        },
    },
    "partnership": {
        "name": "Partnership Agreement",
        "fields": {
            "party_a": "Alpha Ventures",
            "party_b": "Beta Capital",
            "jurisdiction": "United Kingdom",
            "duration": "5 years",
            "purpose": "Joint real estate investment and development fund",
        },
    },
    "freelance": {
        "name": "Freelance / Consulting Agreement",
        "fields": {
            "party_a": "Creative Agency X",
            "party_b": "John Doe (Freelancer)",
            "jurisdiction": "New South Wales, Australia",
            "duration": "6 months",
            "purpose": "UI/UX design and frontend development services",
        },
    },
    "lease": {
        "name": "Commercial Lease Agreement",
        "fields": {
            "party_a": "Prime Properties LLC",
            "party_b": "Startup Ventures Inc.",
            "jurisdiction": "Florida, USA",
            "duration": "2 years",
            "purpose": "Lease of 2,000 sq ft office space at 123 Business Ave",
        },
    },
    "saas": {
        "name": "SaaS Subscription Agreement",
        "fields": {
            "party_a": "CloudSoft Technologies",
            "party_b": "Mid-Market Client Co.",
            "jurisdiction": "Singapore",
            "duration": "Annual (auto-renewing)",
            "purpose": "Access to AI-powered analytics platform — Enterprise Tier",
        },
    },
}


# ---------------------------------------------------------------------------
# Agent 1 — Contract Drafter
# ---------------------------------------------------------------------------

async def agent_contract_drafter(
    client: AsyncOpenAI,
    contract_type: str,
    party_a: str,
    party_b: str,
    jurisdiction: str,
    duration: str,
    purpose: str,
    extra_clauses: str,
    progress: ProgressFn,
) -> str:
    await progress("drafter", "⚖️ Contract Drafter is generating legal language...")

    template_name = CONTRACT_TEMPLATES.get(contract_type, {}).get("name", contract_type.upper())

    system_prompt = """You are a senior corporate attorney specializing in contract law across multiple jurisdictions.
Draft comprehensive, legally-sound contracts with proper structure and professional language.
Always include: Parties section, Recitals/Purpose, Definitions, Core Obligations,
Confidentiality, Intellectual Property, Payment Terms (if applicable),
Term & Termination, Dispute Resolution, Limitation of Liability,
Indemnification, Force Majeure, Governing Law, and Signatures.
Format output as a structured contract with numbered sections and sub-sections."""

    user_prompt = f"""Draft a complete {template_name} with these details:

Party A (First Party): {party_a}
Party B (Second Party): {party_b}
Jurisdiction: {jurisdiction}
Duration: {duration}
Purpose: {purpose}
Additional Clauses Requested: {extra_clauses or 'None'}

Requirements:
- Use professional legal language appropriate for {jurisdiction}
- Include all standard clauses for this contract type
- Number all sections and sub-clauses clearly (e.g., 1., 1.1, 1.2, 2., 2.1, etc.)
- Make it binding and comprehensive
- Include placeholders like [DATE], [SIGNATURE], [TITLE] where needed

Generate the complete contract now:"""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=3000,
    )

    contract_text = response.choices[0].message.content or ""
    await progress("drafter", f"✅ Contract drafted — {len(contract_text.split())} words generated")
    return contract_text


# ---------------------------------------------------------------------------
# Agent 2 — Risk Reviewer
# ---------------------------------------------------------------------------

async def agent_risk_reviewer(
    client: AsyncOpenAI,
    contract_text: str,
    progress: ProgressFn,
) -> list[dict]:
    await progress("reviewer", "🔍 Risk Reviewer is analyzing clauses for legal risk...")

    system_prompt = """You are a legal risk analyst specializing in contract review.
Identify specific clauses or sections that carry legal, financial, or operational risk.
For each risk, provide the clause reference, risk description, severity score 1-10,
and the exact problematic text snippet.
Respond ONLY with valid JSON — no markdown, no extra text."""

    user_prompt = f"""Analyze this contract for legal risks. Return a JSON array of risk objects.
Each object must have exactly these fields:
- "clause": section number or title (string)
- "risk_title": short risk name (string)
- "risk_description": detailed explanation (string)
- "severity": integer 1-10 (10=highest risk)
- "category": one of ["liability", "financial", "compliance", "ip", "termination", "confidentiality", "other"]
- "snippet": the exact risky text from the contract (max 150 chars, string)

Contract to analyze:
{contract_text[:4000]}

Return JSON array only:"""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(raw)
        # Handle both {"risks": [...]} and direct array patterns
        if isinstance(parsed, list):
            risks = parsed
        elif isinstance(parsed, dict):
            # Find the first list value
            risks = next((v for v in parsed.values() if isinstance(v, list)), [])
        else:
            risks = []
    except (json.JSONDecodeError, Exception):
        risks = []

    # Validate and sanitize
    sanitized = []
    for r in risks[:10]:  # cap at 10 risks
        if isinstance(r, dict):
            sanitized.append({
                "clause": str(r.get("clause", "Unknown")),
                "risk_title": str(r.get("risk_title", "Risk Identified")),
                "risk_description": str(r.get("risk_description", "")),
                "severity": int(r.get("severity", 5)) if str(r.get("severity", 5)).isdigit() else 5,
                "category": str(r.get("category", "other")),
                "snippet": str(r.get("snippet", ""))[:200],
            })

    await progress("reviewer", f"✅ Risk Review complete — {len(sanitized)} risks identified")
    return sanitized


# ---------------------------------------------------------------------------
# Agent 3 — Negotiation Advisor
# ---------------------------------------------------------------------------

async def agent_negotiation_advisor(
    client: AsyncOpenAI,
    contract_text: str,
    risks: list[dict],
    progress: ProgressFn,
) -> list[dict]:
    await progress("negotiator", "🤝 Negotiation Advisor is crafting counter-proposals...")

    if not risks:
        await progress("negotiator", "✅ No high-risk clauses found — no negotiations needed")
        return []

    # Focus on high-severity risks (>= 5)
    high_risks = [r for r in risks if r.get("severity", 0) >= 5]
    if not high_risks:
        high_risks = risks[:3]  # at minimum take top 3

    risks_summary = json.dumps(high_risks[:6], indent=2)

    system_prompt = """You are an expert contract negotiator with 20+ years of experience.
For each identified risk, suggest specific replacement language that balances both parties' interests.
Provide practical negotiation strategies. Respond ONLY with valid JSON."""

    user_prompt = f"""For each of these contract risks, provide negotiation advice and suggested replacement language.

Risks to address:
{risks_summary}

Return a JSON array where each object has:
- "clause": the clause reference (string)
- "risk_title": the risk name (string)
- "strategy": negotiation approach in 1-2 sentences (string)
- "suggested_language": the specific replacement text to propose (string)
- "party_a_benefit": how this helps Party A (string)
- "party_b_benefit": how this helps Party B (string)

Return JSON array only:"""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=2500,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            suggestions = parsed
        elif isinstance(parsed, dict):
            suggestions = next((v for v in parsed.values() if isinstance(v, list)), [])
        else:
            suggestions = []
    except (json.JSONDecodeError, Exception):
        suggestions = []

    sanitized = []
    for s in suggestions[:8]:
        if isinstance(s, dict):
            sanitized.append({
                "clause": str(s.get("clause", "Unknown")),
                "risk_title": str(s.get("risk_title", "")),
                "strategy": str(s.get("strategy", "")),
                "suggested_language": str(s.get("suggested_language", "")),
                "party_a_benefit": str(s.get("party_a_benefit", "")),
                "party_b_benefit": str(s.get("party_b_benefit", "")),
            })

    await progress("negotiator", f"✅ Negotiation advice ready — {len(sanitized)} recommendations")
    return sanitized


# ---------------------------------------------------------------------------
# Agent 4 — Plain Language Translator
# ---------------------------------------------------------------------------

async def agent_plain_language_translator(
    client: AsyncOpenAI,
    contract_text: str,
    progress: ProgressFn,
) -> dict:
    await progress("translator", "📝 Plain Language Translator simplifying legal jargon...")

    system_prompt = """You are a legal translator who makes contracts understandable for non-lawyers.
Convert legal jargon into clear, simple English while preserving all important meanings.
Use bullet points for obligations and short paragraphs for explanations."""

    user_prompt = f"""Translate this contract into plain, simple English for a non-lawyer to understand.

Structure your translation as:
1. **What this contract is about** (2-3 sentences)
2. **What Party A (first party) agrees to do** (bullet points)
3. **What Party B (second party) agrees to do** (bullet points)
4. **Important dates and deadlines** (bullet points)
5. **How the contract can end** (bullet points)
6. **What happens if something goes wrong** (bullet points)
7. **Key things to watch out for** (bullet points, max 5 items)

Contract:
{contract_text[:3500]}

Write in plain English:"""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=1500,
    )

    plain_text = response.choices[0].message.content or ""
    word_count = len(contract_text.split())
    plain_word_count = len(plain_text.split())
    reduction = round((1 - plain_word_count / max(word_count, 1)) * 100)

    await progress("translator", f"✅ Translation complete — complexity reduced by ~{reduction}%")
    return {
        "plain_text": plain_text,
        "original_words": word_count,
        "plain_words": plain_word_count,
        "reduction_pct": max(0, reduction),
    }


# ---------------------------------------------------------------------------
# Orchestrator — runs all 4 agents
# ---------------------------------------------------------------------------

class LegalContractSystem:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        self.client = AsyncOpenAI(api_key=key)

    async def run(
        self,
        contract_type: str,
        party_a: str,
        party_b: str,
        jurisdiction: str,
        duration: str,
        purpose: str,
        extra_clauses: str = "",
        progress: ProgressFn = _noop,
    ) -> dict:
        await progress("start", "🚀 Starting AI Legal Contract System — 4 agents initializing...")

        # Agent 1 — Draft contract
        contract_text = await agent_contract_drafter(
            self.client, contract_type, party_a, party_b,
            jurisdiction, duration, purpose, extra_clauses, progress
        )

        # Agents 2, 3, 4 run sequentially (3 depends on 2's output)
        risks = await agent_risk_reviewer(self.client, contract_text, progress)
        negotiations = await agent_negotiation_advisor(self.client, contract_text, risks, progress)
        translation = await agent_plain_language_translator(self.client, contract_text, progress)

        await progress("done", "🎉 All 4 agents complete! Your legal analysis is ready.")

        return {
            "contract_type": contract_type,
            "party_a": party_a,
            "party_b": party_b,
            "jurisdiction": jurisdiction,
            "contract_text": contract_text,
            "risks": risks,
            "negotiations": negotiations,
            "translation": translation,
        }
