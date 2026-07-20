"""AI Startup Validator Crew — six specialized agents run in sequence.

Given a one-sentence startup idea, the crew produces a venture-capital-style
validation:

  1. Market Researcher   — TAM / SAM / SOM sizing and market trends.
  2. Competitor Scout     — existing solutions and differentiation gaps.
  3. Financial Modeler    — a 3-year revenue / cost / profit projection.
  4. Risk Analyst         — a PESTLE risk assessment with mitigations.
  5. Pitch Writer         — an investor-ready elevator pitch and deck outline.
  6. Go/No-Go Scorer      — a weighted verdict with a 0-100 confidence score.

Each agent receives the outputs of the prior agents so its reasoning builds on
the shared context, mimicking a real diligence team. Progress is streamed to the
browser over a WebSocket through an async callback.
"""

from __future__ import annotations

import json
import os
from typing import Awaitable, Callable

from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


class StartupValidatorCrew:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def validate(
        self,
        idea: str,
        industry: str = "",
        stage: str = "idea",
        progress: ProgressFn = _noop,
    ) -> dict:
        idea = (idea or "").strip()
        if len(idea) < 8:
            raise ValueError("Please describe the startup idea in a sentence")

        industry = (industry or "").strip()
        stage = (stage or "idea").strip().lower()

        await progress("start", f"Validating startup: {idea}")

        result: dict = {
            "idea": idea,
            "industry": industry,
            "stage": stage,
        }

        await progress("market", "Market Researcher sizing TAM / SAM / SOM")
        result["market"] = await self._market(idea, industry, stage)

        await progress("competitors", "Competitor Scout mapping existing solutions")
        result["competitors"] = await self._competitors(idea, industry, result)

        await progress("financials", "Financial Modeler building a 3-year forecast")
        result["financials"] = await self._financials(idea, industry, result)

        await progress("risks", "Risk Analyst running a PESTLE assessment")
        result["risks"] = await self._risks(idea, industry, result)

        await progress("pitch", "Pitch Writer drafting the investor pitch")
        result["pitch"] = await self._pitch(idea, industry, result)

        await progress("verdict", "Go/No-Go Scorer computing the final verdict")
        result["verdict"] = await self._verdict(idea, result)

        result = self._post_process(result)
        v = result["verdict"]
        await progress(
            "done",
            f"Verdict: {v['decision']} · score {v['score']}/100",
        )
        return result

    # ----- individual crew members -------------------------------------------

    async def _market(self, idea: str, industry: str, stage: str) -> dict:
        prompt = (
            "You are a senior market research analyst at a VC firm. Size the market for the "
            "startup idea below. Estimate realistic dollar figures. Return ONLY JSON:\n"
            "{\n"
            '  "summary": "2-3 sentence overview of the market opportunity",\n'
            '  "tam_usd": 0, "tam_label": "e.g. $12B",\n'
            '  "sam_usd": 0, "sam_label": "e.g. $2.4B",\n'
            '  "som_usd": 0, "som_label": "e.g. $120M",\n'
            '  "cagr_pct": 0.0,\n'
            '  "target_customer": "who the primary customer is",\n'
            '  "trends": ["market trend or tailwind"],\n'
            '  "headwinds": ["market challenge or headwind"]\n'
            "}\n"
            "TAM = total addressable, SAM = serviceable addressable, SOM = realistic obtainable "
            "in 3 years. Keep the three consistent (TAM > SAM > SOM).\n\n"
            f"INDUSTRY: {industry or 'infer from the idea'}\n"
            f"STAGE: {stage}\n"
            f"STARTUP IDEA: {idea}"
        )
        return await self._json(prompt, temperature=0.5)

    async def _competitors(self, idea: str, industry: str, ctx: dict) -> dict:
        prompt = (
            "You are a competitive intelligence analyst. Identify the main existing solutions the "
            "startup below would compete with, and find the gap it can exploit. Return ONLY JSON:\n"
            "{\n"
            '  "landscape": "2-3 sentence summary of the competitive landscape",\n'
            '  "competitors": [\n'
            '    {"name": "company or product", "positioning": "how they position",\n'
            '     "strength": "their main strength", "weakness": "their main weakness"}\n'
            "  ],\n"
            '  "differentiation": "the wedge / unique angle this startup should own",\n'
            '  "moat": "what could become a durable competitive moat",\n'
            '  "saturation": "low|medium|high"\n'
            "}\n"
            "List 3-5 real, named competitors where possible.\n\n"
            f"MARKET CONTEXT: {ctx['market'].get('summary', '')}\n"
            f"STARTUP IDEA: {idea}"
        )
        return await self._json(prompt, temperature=0.5)

    async def _financials(self, idea: str, industry: str, ctx: dict) -> dict:
        som = ctx["market"].get("som_label", "the obtainable market")
        prompt = (
            "You are a startup financial modeler. Build a realistic 3-year projection for the idea "
            "below. Assume a lean launch. Return ONLY JSON:\n"
            "{\n"
            '  "revenue_model": "how the startup makes money (1-2 sentences)",\n'
            '  "pricing": "headline pricing assumption",\n'
            '  "projections": [\n'
            '    {"year": 1, "customers": 0, "revenue_usd": 0, "costs_usd": 0, "profit_usd": 0}\n'
            "  ],\n"
            '  "seed_ask_usd": 0, "seed_ask_label": "e.g. $500K",\n'
            '  "use_of_funds": ["where the raise goes"],\n'
            '  "break_even": "when the startup plausibly breaks even",\n'
            '  "key_assumptions": ["assumption behind the numbers"]\n'
            "}\n"
            "Provide exactly 3 projection rows (year 1, 2, 3). profit_usd = revenue_usd - costs_usd. "
            "Growth should be ambitious but defensible relative to the obtainable market.\n\n"
            f"OBTAINABLE MARKET (SOM): {som}\n"
            f"REVENUE HINTS FROM COMPETITORS: {ctx['competitors'].get('differentiation', '')}\n"
            f"STARTUP IDEA: {idea}"
        )
        return await self._json(prompt, temperature=0.45)

    async def _risks(self, idea: str, industry: str, ctx: dict) -> dict:
        prompt = (
            "You are a risk analyst using the PESTLE framework (Political, Economic, Social, "
            "Technological, Legal, Environmental). Assess the startup below. Return ONLY JSON:\n"
            "{\n"
            '  "summary": "2-3 sentence risk overview",\n'
            '  "pestle": [\n'
            '    {"category": "Political|Economic|Social|Technological|Legal|Environmental",\n'
            '     "risk": "the specific risk", "severity": "low|medium|high",\n'
            '     "mitigation": "how to reduce or handle it"}\n'
            "  ],\n"
            '  "top_risk": "the single biggest threat to this startup"\n'
            "}\n"
            "Cover the most relevant PESTLE categories (aim for 5-6 entries).\n\n"
            f"MARKET HEADWINDS: {', '.join(ctx['market'].get('headwinds', [])) or 'n/a'}\n"
            f"COMPETITIVE SATURATION: {ctx['competitors'].get('saturation', 'unknown')}\n"
            f"STARTUP IDEA: {idea}"
        )
        return await self._json(prompt, temperature=0.5)

    async def _pitch(self, idea: str, industry: str, ctx: dict) -> dict:
        prompt = (
            "You are a pitch writer for early-stage founders. Using the diligence context, write an "
            "investor-ready pitch for the startup below. Return ONLY JSON:\n"
            "{\n"
            '  "tagline": "one-line hook",\n'
            '  "elevator_pitch": "compelling 3-4 sentence pitch",\n'
            '  "problem": "the problem being solved",\n'
            '  "solution": "the solution in plain terms",\n'
            '  "why_now": "why this is the right moment",\n'
            '  "deck_outline": [\n'
            '    {"slide": "slide title", "content": "one-line of what goes on it"}\n'
            "  ]\n"
            "}\n"
            "Provide a 8-10 slide deck outline (Problem, Solution, Market, Product, Business Model, "
            "Competition, Traction/Roadmap, Team, Ask, etc.).\n\n"
            f"MARKET: {ctx['market'].get('summary', '')}\n"
            f"DIFFERENTIATION: {ctx['competitors'].get('differentiation', '')}\n"
            f"THE ASK: {ctx['financials'].get('seed_ask_label', '')}\n"
            f"STARTUP IDEA: {idea}"
        )
        return await self._json(prompt, temperature=0.6)

    async def _verdict(self, idea: str, ctx: dict) -> dict:
        prompt = (
            "You are a general partner at a VC fund making a go / no-go call on the startup below, "
            "using the full diligence packet. Return ONLY JSON:\n"
            "{\n"
            '  "decision": "GO|CONDITIONAL GO|NO-GO",\n'
            '  "score": 0,\n'
            '  "scores": {\n'
            '    "market": 0, "competition": 0, "financials": 0, "risk": 0, "team_execution": 0\n'
            "  },\n"
            '  "rationale": "3-4 sentence justification of the decision",\n'
            '  "strengths": ["key strength"],\n'
            '  "concerns": ["key concern"],\n'
            '  "conditions": ["what would need to be true to invest"]\n'
            "}\n"
            "Each sub-score is 0-100. `score` is the overall 0-100 confidence. Use GO for >=70, "
            "CONDITIONAL GO for 50-69, NO-GO for <50, and keep `score` consistent with the "
            "decision band.\n\n"
            f"MARKET SOM: {ctx['market'].get('som_label', '')}, CAGR {ctx['market'].get('cagr_pct', 0)}%\n"
            f"COMPETITIVE SATURATION: {ctx['competitors'].get('saturation', 'unknown')}\n"
            f"YEAR-3 PROFIT: {ctx['financials'].get('projections', [{}])[-1].get('profit_usd', 0)}\n"
            f"TOP RISK: {ctx['risks'].get('top_risk', '')}\n"
            f"STARTUP IDEA: {idea}"
        )
        return await self._json(prompt, temperature=0.35)

    # ----- helpers ------------------------------------------------------------

    async def _json(self, prompt: str, temperature: float) -> dict:
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return json.loads(resp.choices[0].message.content)

    def _post_process(self, r: dict) -> dict:
        market = r.setdefault("market", {})
        for k in ("summary", "target_customer"):
            market.setdefault(k, "")
        for k in ("tam_usd", "sam_usd", "som_usd"):
            market[k] = _num(market.get(k))
        market["cagr_pct"] = _num(market.get("cagr_pct"))
        market.setdefault("tam_label", _money(market["tam_usd"]))
        market.setdefault("sam_label", _money(market["sam_usd"]))
        market.setdefault("som_label", _money(market["som_usd"]))
        market.setdefault("trends", [])
        market.setdefault("headwinds", [])

        comp = r.setdefault("competitors", {})
        comp.setdefault("landscape", "")
        comp.setdefault("differentiation", "")
        comp.setdefault("moat", "")
        sat = str(comp.get("saturation", "medium")).lower()
        comp["saturation"] = sat if sat in ("low", "medium", "high") else "medium"
        comp.setdefault("competitors", [])

        fin = r.setdefault("financials", {})
        fin.setdefault("revenue_model", "")
        fin.setdefault("pricing", "")
        fin.setdefault("break_even", "")
        fin.setdefault("use_of_funds", [])
        fin.setdefault("key_assumptions", [])
        fin["seed_ask_usd"] = _num(fin.get("seed_ask_usd"))
        fin.setdefault("seed_ask_label", _money(fin["seed_ask_usd"]))
        rows = []
        for i, p in enumerate(fin.get("projections", []) or [], 1):
            if not isinstance(p, dict):
                continue
            rev = _num(p.get("revenue_usd"))
            cost = _num(p.get("costs_usd"))
            rows.append({
                "year": _num(p.get("year")) or i,
                "customers": _num(p.get("customers")),
                "revenue_usd": rev,
                "costs_usd": cost,
                "profit_usd": p.get("profit_usd") if p.get("profit_usd") is not None else rev - cost,
            })
        for row in rows:
            row["profit_usd"] = _num(row["profit_usd"])
        fin["projections"] = rows

        risks = r.setdefault("risks", {})
        risks.setdefault("summary", "")
        risks.setdefault("top_risk", "")
        clean = []
        for item in risks.get("pestle", []) or []:
            if not isinstance(item, dict) or not item.get("risk"):
                continue
            sev = str(item.get("severity", "medium")).lower()
            item["severity"] = sev if sev in ("low", "medium", "high") else "medium"
            item.setdefault("category", "")
            item.setdefault("mitigation", "")
            clean.append(item)
        risks["pestle"] = clean

        pitch = r.setdefault("pitch", {})
        for k in ("tagline", "elevator_pitch", "problem", "solution", "why_now"):
            pitch.setdefault(k, "")
        pitch.setdefault("deck_outline", [])

        verdict = r.setdefault("verdict", {})
        verdict["score"] = max(0, min(100, _num(verdict.get("score"))))
        scores = verdict.setdefault("scores", {})
        for k in ("market", "competition", "financials", "risk", "team_execution"):
            scores[k] = max(0, min(100, _num(scores.get(k))))
        dec = str(verdict.get("decision", "")).upper().strip()
        if dec not in ("GO", "CONDITIONAL GO", "NO-GO"):
            dec = "GO" if verdict["score"] >= 70 else "CONDITIONAL GO" if verdict["score"] >= 50 else "NO-GO"
        verdict["decision"] = dec
        verdict.setdefault("rationale", "")
        verdict.setdefault("strengths", [])
        verdict.setdefault("concerns", [])
        verdict.setdefault("conditions", [])

        r["stats"] = {
            "tam_label": market["tam_label"],
            "som_label": market["som_label"],
            "competitors": len(comp["competitors"]),
            "risks": len(risks["pestle"]),
            "year3_revenue": _money(rows[-1]["revenue_usd"]) if rows else "$0",
            "score": verdict["score"],
            "decision": verdict["decision"],
        }
        return r


def _num(v) -> float:
    try:
        if isinstance(v, str):
            v = v.replace("$", "").replace(",", "").strip()
        n = float(v)
        return int(n) if n == int(n) else round(n, 2)
    except (TypeError, ValueError):
        return 0


def _money(v) -> str:
    n = _num(v)
    neg = n < 0
    n = abs(n)
    if n >= 1_000_000_000:
        s = f"${n / 1_000_000_000:.1f}B"
    elif n >= 1_000_000:
        s = f"${n / 1_000_000:.1f}M"
    elif n >= 1_000:
        s = f"${n / 1_000:.0f}K"
    else:
        s = f"${n:.0f}"
    return ("-" + s) if neg else s
