"""Autonomous E-Commerce Operations Manager.

Given a product catalog (stock, price, cost, competitor price, weekly sales
history, and customer reviews), five agents manage the store:

  1. Inventory Monitor    — stock health, reorder points, and reorder quantities.
  2. Dynamic Pricing      — competitor-aware repricing that protects margin.
  3. Sales Forecaster     — next-period demand and revenue projection.
  4. Customer Review Analyst — per-product sentiment and drafted responses.
  5. Ad Copy Generator    — platform-specific creatives (Google, Meta, Amazon).

The numeric agents (inventory, pricing, forecasting) run deterministically in
Python so the figures are reproducible; the language agents (reviews, ad copy)
call the model and run concurrently. Progress is streamed to the browser over a
WebSocket through an async callback.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
from typing import Awaitable, Callable

from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Business rules.
MIN_MARGIN = 0.15          # never price below cost * (1 + MIN_MARGIN)
UNDERCUT = 0.02            # price 2% under competitor when profitable
COVER_WEEKS = 4            # reorder to cover this many weeks of demand
MAX_ADCOPY_PRODUCTS = 6    # cap language work for token budget
AD_PLATFORMS = ["Google", "Meta", "Amazon"]

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


class EcommerceManager:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def run(self, catalog: list[dict], progress: ProgressFn = _noop) -> dict:
        products = self._normalize(catalog)
        if not products:
            raise ValueError("Add at least one product to the catalog")

        await progress("start", f"Managing {len(products)} product(s)")

        await progress("inventory", "Inventory Monitor checking stock levels")
        inventory = self._inventory(products)

        await progress("pricing", "Dynamic Pricing Agent comparing competitor prices")
        pricing = self._pricing(products)

        await progress("forecast", "Sales Forecaster projecting demand")
        forecast = self._forecast(products)

        await progress("reviews", "Review Analyst & Ad Copy Generator working")
        reviews, adcopy = await asyncio.gather(
            self._reviews(products),
            self._adcopy(products, pricing),
        )
        await progress("reviews", f"Analyzed reviews for {len(reviews.get('products', []))} product(s)")
        await progress("adcopy", f"Generated ad copy for {len(adcopy.get('products', []))} product(s)")

        result = {
            "products": products,
            "inventory": inventory,
            "pricing": pricing,
            "forecast": forecast,
            "reviews": reviews,
            "adcopy": adcopy,
        }
        result = self._summarize(result)
        s = result["stats"]
        await progress(
            "done",
            f"{s['reorder_alerts']} reorder alert(s) · {s['reprice_count']} reprice(s) · "
            f"forecast revenue {_money(s['forecast_revenue'])}",
        )
        return result

    # ----- normalization ------------------------------------------------------

    def _normalize(self, catalog: list[dict]) -> list[dict]:
        products = []
        for i, p in enumerate(catalog or [], 1):
            if not isinstance(p, dict) or not (p.get("name") or p.get("sku")):
                continue
            hist = [_num(x) for x in (p.get("sales_history") or []) if _is_num(x)]
            reviews = [str(r).strip() for r in (p.get("reviews") or []) if str(r).strip()]
            products.append({
                "sku": str(p.get("sku") or f"SKU-{i}").strip(),
                "name": str(p.get("name") or p.get("sku") or f"Product {i}").strip(),
                "stock": max(0, int(_num(p.get("stock")))),
                "reorder_point": max(0, int(_num(p.get("reorder_point")))),
                "price": round(_num(p.get("price")), 2),
                "cost": round(_num(p.get("cost")), 2),
                "competitor_price": round(_num(p.get("competitor_price")), 2),
                "sales_history": hist,
                "reviews": reviews,
            })
        return products

    # ----- 1. Inventory Monitor (deterministic) --------------------------------

    def _inventory(self, products: list[dict]) -> dict:
        items = []
        alerts = 0
        for p in products:
            weekly = _avg(p["sales_history"])
            daily = weekly / 7 if weekly else 0
            days_left = round(p["stock"] / daily, 1) if daily else None
            rp = p["reorder_point"]
            if p["stock"] <= 0:
                status = "out"
            elif p["stock"] <= rp:
                status = "critical"
            elif p["stock"] <= rp * 1.5:
                status = "low"
            else:
                status = "ok"
            needs = status in ("out", "critical", "low")
            reorder_qty = 0
            if needs and weekly:
                reorder_qty = max(0, int(math.ceil(COVER_WEEKS * weekly) - p["stock"]))
            if needs:
                alerts += 1
            items.append({
                "sku": p["sku"], "name": p["name"], "stock": p["stock"],
                "reorder_point": rp, "avg_weekly_sales": round(weekly, 1),
                "days_of_stock": days_left, "status": status,
                "reorder": needs, "reorder_qty": reorder_qty,
            })
        items.sort(key=lambda x: {"out": 0, "critical": 1, "low": 2, "ok": 3}[x["status"]])
        return {"items": items, "alerts": alerts}

    # ----- 2. Dynamic Pricing (deterministic) ----------------------------------

    def _pricing(self, products: list[dict]) -> dict:
        items = []
        reprices = 0
        for p in products:
            price, cost, comp = p["price"], p["cost"], p["competitor_price"]
            floor = round(cost * (1 + MIN_MARGIN), 2) if cost else 0
            suggested = price
            reason = "Hold — price is competitive."
            if comp > 0 and cost > 0:
                target = round(comp * (1 - UNDERCUT), 2)
                if target < floor:
                    suggested = floor
                    reason = "Raise to protect the minimum margin (competitor is below our floor)."
                elif price > comp:
                    suggested = max(floor, target)
                    reason = "Lower to undercut a cheaper competitor while keeping margin."
                elif price < target:
                    suggested = target
                    reason = "Raise toward the competitor price to capture margin we're leaving on the table."
                else:
                    reason = "Hold — already just under the competitor."
            elif cost > 0 and price < floor:
                suggested = floor
                reason = "Raise to reach the minimum acceptable margin."
            suggested = round(suggested, 2)
            changed = abs(suggested - price) >= 0.01
            if changed:
                reprices += 1
            margin = round((price - cost) / price * 100, 1) if price else 0
            new_margin = round((suggested - cost) / suggested * 100, 1) if suggested else 0
            items.append({
                "sku": p["sku"], "name": p["name"], "price": price,
                "competitor_price": comp, "cost": cost, "floor": floor,
                "suggested_price": suggested, "change": round(suggested - price, 2),
                "margin_pct": margin, "new_margin_pct": new_margin,
                "action": "raise" if suggested > price else "lower" if suggested < price else "hold",
                "reason": reason,
            })
        return {"items": items, "reprices": reprices}

    # ----- 3. Sales Forecaster (deterministic) ---------------------------------

    def _forecast(self, products: list[dict]) -> dict:
        items = []
        total_units = 0.0
        total_rev = 0.0
        for p in products:
            hist = p["sales_history"]
            avg = _avg(hist)
            # Weighted recent average + simple trend from first vs second half.
            if len(hist) >= 2:
                half = len(hist) // 2
                first, second = _avg(hist[:half]), _avg(hist[half:])
                trend = "up" if second > first * 1.05 else "down" if second < first * 0.95 else "flat"
                recent = _avg(hist[-3:]) if len(hist) >= 3 else second
                factor = 1 + max(-0.4, min(0.4, (second - first) / first)) if first else 1
                next_units = max(0, round(recent * factor))
            else:
                trend = "flat"
                next_units = max(0, round(avg))
            rev = round(next_units * p["price"], 2)
            total_units += next_units
            total_rev += rev
            items.append({
                "sku": p["sku"], "name": p["name"], "history": hist,
                "avg_weekly": round(avg, 1), "trend": trend,
                "forecast_units": int(next_units), "forecast_revenue": rev,
            })
        items.sort(key=lambda x: x["forecast_revenue"], reverse=True)
        return {
            "items": items,
            "total_units": int(total_units),
            "total_revenue": round(total_rev, 2),
        }

    # ----- 4. Customer Review Analyst (LLM) ------------------------------------

    async def _reviews(self, products: list[dict]) -> dict:
        payload = [
            {"sku": p["sku"], "name": p["name"], "reviews": p["reviews"]}
            for p in products if p["reviews"]
        ]
        if not payload:
            return {"products": [], "overall": "No customer reviews provided."}
        prompt = (
            "You are a customer experience analyst for an online store. Analyze the reviews for each "
            "product. Return ONLY JSON:\n"
            "{\n"
            '  "overall": "1-2 sentence store-wide sentiment summary",\n'
            '  "products": [\n'
            "    {\n"
            '      "sku": "matching sku",\n'
            '      "sentiment": "positive|mixed|negative",\n'
            '      "score": 0,\n'
            '      "themes": ["recurring theme customers mention"],\n'
            '      "response_draft": "a warm, professional public reply addressing the main concern"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "score is 0-100 (customer satisfaction). Write the response_draft to defuse negatives and "
            "thank positives.\n\n"
            f"REVIEWS:\n{json.dumps(payload, indent=2)[:12000]}"
        )
        return await self._json(prompt, 0.4)

    # ----- 5. Ad Copy Generator (LLM) ------------------------------------------

    async def _adcopy(self, products: list[dict], pricing: dict) -> dict:
        price_by_sku = {i["sku"]: i["suggested_price"] for i in pricing["items"]}
        payload = [
            {"sku": p["sku"], "name": p["name"], "price": price_by_sku.get(p["sku"], p["price"])}
            for p in products[:MAX_ADCOPY_PRODUCTS]
        ]
        prompt = (
            "You are a performance-marketing copywriter. Write ad creatives for each product tailored "
            f"to these platforms: {', '.join(AD_PLATFORMS)}. Return ONLY JSON:\n"
            "{\n"
            '  "products": [\n'
            "    {\n"
            '      "sku": "matching sku",\n'
            '      "ads": [\n'
            '        {"platform": "Google", "headline": "<=30 chars", "body": "<=90 chars",\n'
            '         "cta": "short call to action"}\n'
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Give one ad per platform per product. Respect Google's short headline limit; Meta can be "
            "punchier and emotive; Amazon should be benefit- and feature-led.\n\n"
            f"PRODUCTS:\n{json.dumps(payload, indent=2)[:8000]}"
        )
        return await self._json(prompt, 0.7)

    # ----- helpers -------------------------------------------------------------

    async def _json(self, prompt: str, temperature: float) -> dict:
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return json.loads(resp.choices[0].message.content)

    def _summarize(self, r: dict) -> dict:
        inv, pr, fc = r["inventory"], r["pricing"], r["forecast"]

        # Clean review output.
        reviews = r.setdefault("reviews", {})
        reviews.setdefault("overall", "")
        clean_rev = []
        for item in reviews.get("products", []) or []:
            if not isinstance(item, dict):
                continue
            sent = str(item.get("sentiment", "mixed")).lower()
            item["sentiment"] = sent if sent in ("positive", "mixed", "negative") else "mixed"
            item["score"] = _clamp(item.get("score"))
            item.setdefault("themes", [])
            item.setdefault("response_draft", "")
            clean_rev.append(item)
        reviews["products"] = clean_rev

        # Clean ad copy output.
        adcopy = r.setdefault("adcopy", {})
        clean_ads = []
        for item in adcopy.get("products", []) or []:
            if not isinstance(item, dict):
                continue
            ads = [a for a in (item.get("ads") or []) if isinstance(a, dict) and a.get("headline")]
            item["ads"] = ads
            clean_ads.append(item)
        adcopy["products"] = clean_ads

        potential_gain = round(sum(
            i["change"] * next((it["forecast_units"] for it in fc["items"] if it["sku"] == i["sku"]), 0)
            for i in pr["items"]
        ), 2)

        avg_score = round(
            sum(x["score"] for x in clean_rev) / len(clean_rev)
        ) if clean_rev else None

        r["stats"] = {
            "products": len(r["products"]),
            "reorder_alerts": inv["alerts"],
            "reprice_count": pr["reprices"],
            "forecast_units": fc["total_units"],
            "forecast_revenue": fc["total_revenue"],
            "reprice_revenue_delta": potential_gain,
            "avg_review_score": avg_score,
            "out_of_stock": sum(1 for i in inv["items"] if i["status"] == "out"),
        }
        return r


# ----- module utilities -------------------------------------------------------

def _avg(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _is_num(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _num(v) -> float:
    try:
        if isinstance(v, str):
            v = v.replace("$", "").replace(",", "").strip()
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
        s = f"${n / 1_000_000:.1f}M"
    elif n >= 1_000:
        s = f"${n / 1_000:.1f}K"
    else:
        s = f"${n:.2f}"
    return ("-" + s) if neg else s
