"""AI trading signal & portfolio analyzer agent.

For each requested symbol the agent:
  1. Fetches real OHLCV history via yfinance.
  2. Computes technical indicators (RSI, MACD, EMA, Bollinger Bands).
  3. Asks OpenAI to turn that indicator snapshot into a BUY/SELL/HOLD
     signal with a confidence score and plain-English rationale.

When multiple symbols are given it also produces a portfolio-level risk and
diversification assessment.

Progress is reported through an async callback so the FastAPI layer can
stream it to the browser over a WebSocket.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Awaitable, Callable

from openai import AsyncOpenAI

import indicators
from market import MarketDataError, fetch_history

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ProgressFn = Callable[[str, str], Awaitable[None]]

VALID_SIGNALS = {"BUY", "SELL", "HOLD"}


async def _noop(stage: str, message: str) -> None:
    return None


class TradingAgent:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def analyze(
        self,
        symbols: list[str],
        period: str = "1y",
        progress: ProgressFn = _noop,
    ) -> dict:
        symbols = [s.strip().upper() for s in symbols if s and s.strip()]
        # De-dupe while preserving order.
        symbols = list(dict.fromkeys(symbols))
        if not symbols:
            raise ValueError("No symbols provided")

        await progress("start", f"Analyzing {len(symbols)} symbol(s): {', '.join(symbols)}")

        assets: list[dict] = []
        errors: list[dict] = []
        for sym in symbols:
            try:
                await progress("fetch", f"Fetching market data for {sym}")
                data = await asyncio.to_thread(fetch_history, sym, period)
                closes = [c["close"] for c in data["candles"]]
                snap = indicators.summarize(closes)
                await progress(
                    "indicators",
                    f"{sym}: price {snap['price']} · RSI {snap['rsi']} · "
                    f"MACD hist {snap['macd']['histogram']}",
                )
                signal = await self._signal(data, snap, progress)
                assets.append({
                    "symbol": data["symbol"],
                    "name": data["name"],
                    "currency": data["currency"],
                    "candles": data["candles"],
                    "indicators": snap,
                    "signal": signal,
                })
            except MarketDataError as exc:
                errors.append({"symbol": sym, "error": str(exc)})
                await progress("fetch", f"✗ {sym}: {exc}")
            except Exception as exc:  # noqa: BLE001
                errors.append({"symbol": sym, "error": str(exc)})
                await progress("fetch", f"✗ {sym}: {exc}")

        if not assets:
            raise ValueError(
                "Could not analyze any symbols. " + (errors[0]["error"] if errors else "")
            )

        portfolio = None
        if len(assets) > 1:
            await progress("portfolio", "Assessing portfolio risk & diversification")
            portfolio = await self._portfolio(assets)

        await progress("done", f"Generated signals for {len(assets)} symbol(s)")
        return {"assets": assets, "errors": errors, "portfolio": portfolio}

    async def _signal(self, data: dict, snap: dict, progress: ProgressFn) -> dict:
        prompt = (
            "You are a technical analyst. Based ONLY on the indicator snapshot "
            f"below for {data['symbol']} ({data['name']}), produce a trading "
            "signal. Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "signal": "BUY|SELL|HOLD",\n'
            '  "confidence": 0-100,\n'
            '  "rationale": "2-3 sentence explanation grounded in the indicators",\n'
            '  "bull_case": ["short bullish point"],\n'
            '  "bear_case": ["short bearish point"],\n'
            '  "risk_level": "low|medium|high",\n'
            '  "time_horizon": "e.g. short-term (days), swing (weeks), long-term"\n'
            "}\n"
            "Interpret RSI (>70 overbought, <30 oversold), MACD histogram sign & momentum, "
            "price vs EMA50/EMA200 (trend), and Bollinger percent_b (near 1 = upper band). "
            "Higher confidence only when multiple indicators agree.\n\n"
            f"Indicators: {json.dumps(snap)}"
        )
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        d = json.loads(resp.choices[0].message.content)
        sig = str(d.get("signal", "HOLD")).upper()
        if sig not in VALID_SIGNALS:
            sig = "HOLD"
        d["signal"] = sig
        d["confidence"] = max(0, min(100, int(d.get("confidence") or 0)))
        d.setdefault("rationale", "")
        d.setdefault("bull_case", [])
        d.setdefault("bear_case", [])
        d.setdefault("risk_level", "medium")
        d.setdefault("time_horizon", "")
        await progress("signal", f"{data['symbol']}: {sig} ({d['confidence']}% confidence)")
        return d

    async def _portfolio(self, assets: list[dict]) -> dict:
        rows = [
            {
                "symbol": a["symbol"],
                "signal": a["signal"]["signal"],
                "confidence": a["signal"]["confidence"],
                "risk_level": a["signal"]["risk_level"],
                "rsi": a["indicators"]["rsi"],
                "change_30d_pct": a["indicators"]["change_30d_pct"],
            }
            for a in assets
        ]
        prompt = (
            "You are a portfolio risk manager. Given the per-asset signals below, "
            "assess the portfolio as a whole. Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "risk_score": 0-100,\n'
            '  "risk_level": "low|medium|high",\n'
            '  "diversification": "one-sentence assessment of concentration/correlation risk",\n'
            '  "summary": "2-3 sentence overview of the portfolio posture",\n'
            '  "recommendations": ["actionable rebalancing/risk recommendation"]\n'
            "}\n"
            "Higher risk_score = more risk (concentration, many high-risk or SELL assets).\n\n"
            f"Assets: {json.dumps(rows)}"
        )
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        d = json.loads(resp.choices[0].message.content)
        d["risk_score"] = max(0, min(100, int(d.get("risk_score") or 0)))
        d.setdefault("risk_level", "medium")
        d.setdefault("diversification", "")
        d.setdefault("summary", "")
        d.setdefault("recommendations", [])
        return d
