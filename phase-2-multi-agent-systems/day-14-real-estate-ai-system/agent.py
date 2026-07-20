"""AI Real Estate Investment Analyzer.

Given a property address, a purchase budget, and a few property details, five
agents evaluate the deal:

  1. Market Valuation      — estimated value, price/sqft, comparables, trend.
  2. Rental Projection     — long-term vs short-term (Airbnb) monthly income.
  3. Neighborhood Analysis — 8-dimension livability scoring.
  4. ROI Calculator        — cap rate, cash-on-cash return, monthly cash flow.
  5. Investment Report     — a verdict and narrative synthesizing the above.

The three analytical agents call the model and run concurrently; the ROI agent
computes deterministically from their figures; the report agent runs last on the
full picture. The address is geocoded (OpenStreetMap Nominatim) so the UI can
drop a map pin. Progress streams over a WebSocket through an async callback.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Awaitable, Callable

import httpx
from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Financing / cost assumptions (typical US residential investment defaults).
DOWN_PCT = 0.25            # 25% down payment
RATE = 0.07               # 7% annual mortgage rate
TERM_YEARS = 30
CLOSING_PCT = 0.03         # 3% of price in closing costs
VACANCY_PCT = 0.06         # 6% vacancy allowance
MGMT_PCT = 0.08            # 8% property management (of rent)
MAINT_PCT = 0.10           # 10% maintenance reserve (of rent)
TAX_PCT = 0.011            # 1.1% annual property tax (of value)
INSURANCE_PCT = 0.005      # 0.5% annual insurance (of value)

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


class RealEstateAnalyzer:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def analyze(
        self,
        address: str,
        budget: float = 0,
        beds: int = 3,
        baths: int = 2,
        sqft: int = 1500,
        property_type: str = "single-family home",
        progress: ProgressFn = _noop,
    ) -> dict:
        address = (address or "").strip()
        if len(address) < 5:
            raise ValueError("Enter a property address")

        budget = max(0, _num(budget))
        beds = max(0, int(_num(beds)))
        baths = max(0, _num(baths))
        sqft = max(1, int(_num(sqft)))
        property_type = (property_type or "single-family home").strip()

        prop = {
            "address": address, "budget": budget, "beds": beds, "baths": baths,
            "sqft": sqft, "property_type": property_type,
        }

        await progress("start", f"Analyzing {address}")

        await progress("geocode", "Locating the property on the map")
        prop["geo"] = await self._geocode(address)

        await progress("valuation", "Valuation, Rental & Neighborhood agents running")
        valuation, rental, neighborhood = await asyncio.gather(
            self._valuation(prop),
            self._rental(prop),
            self._neighborhood(prop),
        )
        await progress("valuation", f"Estimated value {_money(valuation.get('estimated_value'))}")
        await progress("rental", f"Long-term rent ~{_money(rental.get('long_term_monthly'))}/mo")
        await progress("neighborhood", f"Neighborhood score {neighborhood.get('overall_score')}/100")

        await progress("roi", "ROI Calculator running the numbers")
        roi = self._roi(prop, valuation, rental)

        result = {
            "property": prop,
            "valuation": valuation,
            "rental": rental,
            "neighborhood": neighborhood,
            "roi": roi,
        }
        result = self._post_process(result)

        await progress("report", "Investment Report Writer drafting the verdict")
        result["report"] = await self._report(result)
        result = self._finalize(result)

        r = result["report"]
        await progress("done", f"Verdict: {r['recommendation']} · deal score {result['stats']['deal_score']}/100")
        return result

    # ----- geocoding ----------------------------------------------------------

    async def _geocode(self, address: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": address, "format": "json", "limit": 1},
                    headers={"User-Agent": "real-estate-analyzer/1.0"},
                )
                resp.raise_for_status()
                hits = resp.json()
                if hits:
                    h = hits[0]
                    return {
                        "lat": float(h["lat"]), "lon": float(h["lon"]),
                        "display_name": h.get("display_name", address),
                    }
        except Exception:
            pass
        return {"lat": None, "lon": None, "display_name": address}

    # ----- LLM agents ---------------------------------------------------------

    async def _valuation(self, p: dict) -> dict:
        prompt = (
            "You are a real estate appraiser. Estimate the market value of the property below using "
            "your knowledge of the area. Return ONLY JSON:\n"
            "{\n"
            '  "estimated_value": 0,\n'
            '  "price_per_sqft": 0,\n'
            '  "confidence": "low|medium|high",\n'
            '  "market_trend": "rising|stable|cooling",\n'
            '  "yoy_change_pct": 0.0,\n'
            '  "comparables": [\n'
            '    {"desc": "e.g. 3bd/2ba 0.3mi away", "price": 0, "sqft": 0}\n'
            "  ],\n"
            '  "notes": "1-2 sentence valuation rationale"\n'
            "}\n"
            "Give 3 realistic comparables for the area. Base price_per_sqft on the estimated_value and "
            "the property's sqft.\n\n"
            + _prop_block(p)
        )
        return await self._json(prompt, 0.4)

    async def _rental(self, p: dict) -> dict:
        prompt = (
            "You are a rental market analyst. Estimate rental income for the property below, both as a "
            "long-term lease and as a short-term (Airbnb-style) rental. Return ONLY JSON:\n"
            "{\n"
            '  "long_term_monthly": 0,\n'
            '  "short_term_nightly": 0,\n'
            '  "short_term_occupancy_pct": 0,\n'
            '  "short_term_monthly": 0,\n'
            '  "recommended_strategy": "long-term|short-term",\n'
            '  "notes": "1-2 sentence rationale comparing the two"\n'
            "}\n"
            "short_term_monthly should reflect nightly rate x 30 x occupancy. Recommend the strategy "
            "with the better risk-adjusted return for this location.\n\n"
            + _prop_block(p)
        )
        return await self._json(prompt, 0.4)

    async def _neighborhood(self, p: dict) -> dict:
        prompt = (
            "You are a neighborhood analyst. Score the area around the property below across 8 "
            "dimensions (0-100 each). Return ONLY JSON:\n"
            "{\n"
            '  "overall_score": 0,\n'
            '  "scores": {\n'
            '    "safety": 0, "schools": 0, "amenities": 0, "transit": 0,\n'
            '    "walkability": 0, "employment": 0, "affordability": 0, "growth": 0\n'
            "  },\n"
            '  "highlights": ["a positive feature of the area"],\n'
            '  "concerns": ["a drawback of the area"],\n'
            '  "summary": "1-2 sentence neighborhood assessment"\n'
            "}\n"
            "overall_score should roughly reflect the average of the 8 sub-scores.\n\n"
            + _prop_block(p)
        )
        return await self._json(prompt, 0.4)

    async def _report(self, r: dict) -> dict:
        roi = r["roi"]
        prompt = (
            "You are a real estate investment advisor. Given the analysis below, write the investment "
            "verdict for this property. Return ONLY JSON:\n"
            "{\n"
            '  "recommendation": "STRONG BUY|BUY|HOLD|PASS",\n'
            '  "deal_score": 0,\n'
            '  "thesis": "3-4 sentence investment thesis",\n'
            '  "pros": ["a reason to invest"],\n'
            '  "cons": ["a risk or downside"],\n'
            '  "best_strategy": "how to maximize return on this property",\n'
            '  "exit_notes": "resale / exit outlook in 1-2 sentences"\n'
            "}\n"
            "deal_score is 0-100. Weight cash flow, cap rate, cash-on-cash return, neighborhood "
            "quality, and market trend. STRONG BUY >=80, BUY 65-79, HOLD 50-64, PASS <50; keep "
            "deal_score consistent with the recommendation.\n\n"
            f"PURCHASE PRICE: {_money(roi.get('purchase_price'))}\n"
            f"ESTIMATED VALUE: {_money(r['valuation'].get('estimated_value'))} "
            f"(trend: {r['valuation'].get('market_trend')})\n"
            f"MONTHLY CASH FLOW: {_money(roi.get('monthly_cash_flow'))}\n"
            f"CAP RATE: {roi.get('cap_rate_pct')}% · CASH-ON-CASH: {roi.get('cash_on_cash_pct')}%\n"
            f"RECOMMENDED RENTAL: {r['rental'].get('recommended_strategy')}\n"
            f"NEIGHBORHOOD SCORE: {r['neighborhood'].get('overall_score')}/100\n"
            f"ADDRESS: {r['property']['address']}"
        )
        return await self._json(prompt, 0.35)

    # ----- ROI (deterministic) ------------------------------------------------

    def _roi(self, p: dict, valuation: dict, rental: dict) -> dict:
        value = _num(valuation.get("estimated_value"))
        price = p["budget"] if p["budget"] > 0 else value
        if price <= 0:
            price = value

        wants_short = "short" in str(rental.get("recommended_strategy", "long-term")).lower()
        lt = _num(rental.get("long_term_monthly"))
        stm = _num(rental.get("short_term_monthly"))
        use_short = wants_short and stm > 0
        gross_monthly = stm if use_short else lt
        gross_annual = gross_monthly * 12

        # Operating expenses (annual).
        vacancy = gross_annual * VACANCY_PCT
        mgmt = gross_annual * MGMT_PCT
        maint = gross_annual * MAINT_PCT
        tax = price * TAX_PCT
        insurance = price * INSURANCE_PCT
        opex = vacancy + mgmt + maint + tax + insurance
        noi = gross_annual - opex

        # Financing.
        down = price * DOWN_PCT
        loan = price - down
        closing = price * CLOSING_PCT
        monthly_rate = RATE / 12
        n = TERM_YEARS * 12
        if loan > 0 and monthly_rate > 0:
            mortgage_monthly = loan * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)
        else:
            mortgage_monthly = 0
        mortgage_annual = mortgage_monthly * 12

        annual_cash_flow = noi - mortgage_annual
        monthly_cash_flow = annual_cash_flow / 12
        cash_invested = down + closing
        cap_rate = (noi / price * 100) if price else 0
        coc = (annual_cash_flow / cash_invested * 100) if cash_invested else 0
        grm = (price / gross_annual) if gross_annual else 0

        return {
            "purchase_price": round(price, 2),
            "rental_strategy": "short-term" if use_short else "long-term",
            "gross_monthly_rent": round(gross_monthly, 2),
            "noi_annual": round(noi, 2),
            "operating_expenses_annual": round(opex, 2),
            "expense_breakdown": {
                "vacancy": round(vacancy, 2), "management": round(mgmt, 2),
                "maintenance": round(maint, 2), "property_tax": round(tax, 2),
                "insurance": round(insurance, 2),
            },
            "down_payment": round(down, 2),
            "loan_amount": round(loan, 2),
            "closing_costs": round(closing, 2),
            "cash_invested": round(cash_invested, 2),
            "mortgage_monthly": round(mortgage_monthly, 2),
            "monthly_cash_flow": round(monthly_cash_flow, 2),
            "annual_cash_flow": round(annual_cash_flow, 2),
            "cap_rate_pct": round(cap_rate, 2),
            "cash_on_cash_pct": round(coc, 2),
            "gross_rent_multiplier": round(grm, 1),
            "assumptions": {
                "down_pct": DOWN_PCT, "rate_pct": RATE * 100, "term_years": TERM_YEARS,
                "vacancy_pct": VACANCY_PCT * 100, "mgmt_pct": MGMT_PCT * 100,
                "maint_pct": MAINT_PCT * 100,
            },
        }

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
        v = r["valuation"]
        v["estimated_value"] = round(_num(v.get("estimated_value")), 2)
        v["price_per_sqft"] = round(_num(v.get("price_per_sqft")), 2)
        if not v["price_per_sqft"] and v["estimated_value"]:
            v["price_per_sqft"] = round(v["estimated_value"] / max(1, r["property"]["sqft"]), 2)
        v["yoy_change_pct"] = round(_num(v.get("yoy_change_pct")), 2)
        conf = str(v.get("confidence", "medium")).lower()
        v["confidence"] = conf if conf in ("low", "medium", "high") else "medium"
        trend = str(v.get("market_trend", "stable")).lower()
        v["market_trend"] = trend if trend in ("rising", "stable", "cooling") else "stable"
        v.setdefault("notes", "")
        comps = []
        for c in v.get("comparables", []) or []:
            if isinstance(c, dict) and c.get("desc"):
                c["price"] = round(_num(c.get("price")), 2)
                c["sqft"] = int(_num(c.get("sqft")))
                comps.append(c)
        v["comparables"] = comps

        rl = r["rental"]
        for k in ("long_term_monthly", "short_term_nightly", "short_term_monthly"):
            rl[k] = round(_num(rl.get(k)), 2)
        rl["short_term_occupancy_pct"] = round(_num(rl.get("short_term_occupancy_pct")), 1)
        strat = str(rl.get("recommended_strategy", "long-term")).lower()
        rl["recommended_strategy"] = "short-term" if "short" in strat else "long-term"
        rl.setdefault("notes", "")

        n = r["neighborhood"]
        scores = n.setdefault("scores", {})
        for k in ("safety", "schools", "amenities", "transit", "walkability",
                  "employment", "affordability", "growth"):
            scores[k] = _clamp(scores.get(k))
        n["overall_score"] = _clamp(n.get("overall_score")) or (
            round(sum(scores.values()) / len(scores)) if scores else 0)
        n.setdefault("highlights", [])
        n.setdefault("concerns", [])
        n.setdefault("summary", "")
        return r

    def _finalize(self, r: dict) -> dict:
        rep = r["report"]
        rep["deal_score"] = _clamp(rep.get("deal_score"))
        rec = str(rep.get("recommendation", "")).upper().strip()
        if rec not in ("STRONG BUY", "BUY", "HOLD", "PASS"):
            sc = rep["deal_score"]
            rec = "STRONG BUY" if sc >= 80 else "BUY" if sc >= 65 else "HOLD" if sc >= 50 else "PASS"
        rep["recommendation"] = rec
        rep.setdefault("thesis", "")
        rep.setdefault("pros", [])
        rep.setdefault("cons", [])
        rep.setdefault("best_strategy", "")
        rep.setdefault("exit_notes", "")

        roi = r["roi"]
        r["stats"] = {
            "estimated_value": r["valuation"]["estimated_value"],
            "purchase_price": roi["purchase_price"],
            "monthly_cash_flow": roi["monthly_cash_flow"],
            "cap_rate_pct": roi["cap_rate_pct"],
            "cash_on_cash_pct": roi["cash_on_cash_pct"],
            "neighborhood_score": r["neighborhood"]["overall_score"],
            "deal_score": rep["deal_score"],
            "recommendation": rep["recommendation"],
        }
        return r


# ----- module utilities -------------------------------------------------------

def _prop_block(p: dict) -> str:
    budget = f"buyer budget {_money(p['budget'])}" if p["budget"] else "budget not specified"
    return (
        f"PROPERTY:\n"
        f"- Address: {p['address']}\n"
        f"- Type: {p['property_type']}\n"
        f"- {p['beds']} bed / {p['baths']} bath · {p['sqft']} sqft\n"
        f"- {budget}"
    )


def _num(v) -> float:
    try:
        if isinstance(v, str):
            v = v.replace("$", "").replace(",", "").replace("%", "").strip()
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _clamp(v) -> int:
    try:
        return max(0, min(100, int(float(v))))
    except (TypeError, ValueError):
        return 0


def _money(v) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "$0"
    neg = n < 0
    n = abs(n)
    if n >= 1_000_000:
        s = f"${n / 1_000_000:.2f}M"
    elif n >= 1_000:
        s = f"${n / 1_000:.0f}K"
    else:
        s = f"${n:.0f}"
    return ("-" + s) if neg else s
