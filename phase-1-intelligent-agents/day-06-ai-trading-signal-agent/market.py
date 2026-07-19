"""Fetch OHLCV market data for stocks and crypto via yfinance.

yfinance is synchronous, so callers should run these in a thread
(e.g. asyncio.to_thread) to avoid blocking the event loop.
"""

from __future__ import annotations


class MarketDataError(Exception):
    pass


def fetch_history(symbol: str, period: str = "1y", interval: str = "1d") -> dict:
    """Return {'symbol','name','currency','candles':[{time,open,high,low,close,volume}]}.

    `symbol` may be a stock ticker (AAPL) or a yfinance crypto pair (BTC-USD).
    """
    import yfinance as yf

    symbol = symbol.strip().upper()
    if not symbol:
        raise MarketDataError("No symbol provided")

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval, auto_adjust=True)
    if hist is None or hist.empty:
        raise MarketDataError(
            f"No data for '{symbol}'. Use a valid ticker (e.g. AAPL) or crypto pair (e.g. BTC-USD)."
        )

    candles: list[dict] = []
    for idx, row in hist.iterrows():
        try:
            candles.append({
                "time": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if row["Volume"] == row["Volume"] else 0,
            })
        except (ValueError, KeyError):
            continue

    if not candles:
        raise MarketDataError(f"Could not parse price data for '{symbol}'")

    name, currency = symbol, "USD"
    try:
        info = ticker.fast_info
        currency = getattr(info, "currency", None) or "USD"
    except Exception:
        pass
    try:
        meta = ticker.info
        name = meta.get("shortName") or meta.get("longName") or symbol
    except Exception:
        pass

    return {"symbol": symbol, "name": name, "currency": currency, "candles": candles}
