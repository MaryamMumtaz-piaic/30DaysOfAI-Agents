"""Technical indicator calculations over an OHLCV price series.

Pure-Python (no pandas dependency at call sites) so the agent can compute
RSI, MACD, EMA, SMA, and Bollinger Bands from a plain list of closes/candles.
"""

from __future__ import annotations


def ema(values: list[float], period: int) -> list[float]:
    """Exponential moving average; returns a series aligned to `values`."""
    if not values:
        return []
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def sma(values: list[float], period: int) -> list[float | None]:
    out: list[float | None] = []
    run = 0.0
    for i, v in enumerate(values):
        run += v
        if i >= period:
            run -= values[i - period]
        out.append(run / period if i >= period - 1 else None)
    return out


def rsi(closes: list[float], period: int = 14) -> float | None:
    """Wilder's RSI on the most recent value (0-100)."""
    if len(closes) < period + 1:
        return None
    gains, losses = 0.0, 0.0
    for i in range(1, period + 1):
        diff = closes[i] - closes[i - 1]
        gains += max(diff, 0)
        losses += max(-diff, 0)
    avg_gain = gains / period
    avg_loss = losses / period
    for i in range(period + 1, len(closes)):
        diff = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(diff, 0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-diff, 0)) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Return the latest MACD line, signal line, and histogram."""
    if len(closes) < slow + signal:
        return {"macd": None, "signal": None, "histogram": None}
    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema(macd_line, signal)
    return {
        "macd": round(macd_line[-1], 4),
        "signal": round(signal_line[-1], 4),
        "histogram": round(macd_line[-1] - signal_line[-1], 4),
    }


def bollinger(closes: list[float], period: int = 20, mult: float = 2.0) -> dict:
    if len(closes) < period:
        return {"upper": None, "middle": None, "lower": None, "percent_b": None}
    window = closes[-period:]
    mid = sum(window) / period
    var = sum((c - mid) ** 2 for c in window) / period
    sd = var ** 0.5
    upper = mid + mult * sd
    lower = mid - mult * sd
    last = closes[-1]
    pct_b = (last - lower) / (upper - lower) if upper != lower else 0.5
    return {
        "upper": round(upper, 2),
        "middle": round(mid, 2),
        "lower": round(lower, 2),
        "percent_b": round(pct_b, 3),
    }


def summarize(closes: list[float]) -> dict:
    """Compute the full indicator snapshot used to drive the signal."""
    last = closes[-1]
    ema20 = ema(closes, 20)[-1] if len(closes) >= 20 else None
    ema50 = ema(closes, 50)[-1] if len(closes) >= 50 else None
    ema200 = ema(closes, 200)[-1] if len(closes) >= 200 else None
    change_1d = _pct(closes[-1], closes[-2]) if len(closes) >= 2 else None
    change_7 = _pct(closes[-1], closes[-8]) if len(closes) >= 8 else None
    change_30 = _pct(closes[-1], closes[-31]) if len(closes) >= 31 else None
    return {
        "price": round(last, 2),
        "rsi": rsi(closes),
        "macd": macd(closes),
        "bollinger": bollinger(closes),
        "ema20": round(ema20, 2) if ema20 else None,
        "ema50": round(ema50, 2) if ema50 else None,
        "ema200": round(ema200, 2) if ema200 else None,
        "above_ema50": (last > ema50) if ema50 else None,
        "above_ema200": (last > ema200) if ema200 else None,
        "change_1d_pct": change_1d,
        "change_7d_pct": change_7,
        "change_30d_pct": change_30,
    }


def _pct(now: float, then: float) -> float | None:
    if not then:
        return None
    return round((now - then) / then * 100, 2)
