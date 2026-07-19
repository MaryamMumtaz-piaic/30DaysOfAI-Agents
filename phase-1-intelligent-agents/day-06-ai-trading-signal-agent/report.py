"""Render a trading-signal analysis into a professional PDF report."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#0891b2")   # cyan-600
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")

SIGNAL_INK = {
    "BUY": colors.HexColor("#065f46"),
    "SELL": colors.HexColor("#991b1b"),
    "HOLD": colors.HexColor("#92400e"),
}
SIGNAL_BG = {
    "BUY": colors.HexColor("#ecfdf5"),
    "SELL": colors.HexColor("#fef2f2"),
    "HOLD": colors.HexColor("#fffbeb"),
}


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("T", parent=base["Title"], fontSize=22,
                                 textColor=ACCENT, spaceAfter=4),
        "subtitle": ParagraphStyle("S", parent=base["Normal"], fontSize=10,
                                   textColor=MUTED, spaceAfter=12),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontSize=14,
                             textColor=INK, spaceBefore=16, spaceAfter=6),
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontSize=12,
                             textColor=ACCENT, spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("B", parent=base["Normal"], fontSize=10,
                               leading=15, alignment=TA_JUSTIFY, spaceAfter=6),
        "item": ParagraphStyle("I", parent=base["Normal"], fontSize=9.5,
                               leading=14, alignment=TA_LEFT),
        "cell": ParagraphStyle("C", parent=base["Normal"], fontSize=9, leading=12),
        "cellh": ParagraphStyle("CH", parent=base["Normal"], fontSize=9,
                                leading=12, textColor=colors.white),
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5,
                               textColor=MUTED),
    }


def _bar(pct: int, color: colors.Color, width: float = 40 * mm) -> Table:
    pct = max(0, min(100, int(pct or 0)))
    filled = width * pct / 100
    empty = width - filled
    inner = Table([["", ""]], colWidths=[filled or 0.1, empty or 0.1], rowHeights=[6])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return inner


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Trading Signals Report",
    )
    st = _styles()
    flow: list = []
    assets = data.get("assets", [])
    portfolio = data.get("portfolio")

    flow.append(Paragraph("AI Trading Signals Report", st["title"]))
    flow.append(Paragraph(
        f"{len(assets)} asset(s) analyzed  ·  "
        f"{sum(1 for a in assets if a['signal']['signal']=='BUY')} BUY · "
        f"{sum(1 for a in assets if a['signal']['signal']=='SELL')} SELL · "
        f"{sum(1 for a in assets if a['signal']['signal']=='HOLD')} HOLD", st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Signals summary table
    flow.append(Paragraph("Signals Overview", st["h2"]))
    rows = [[Paragraph("<b>Symbol</b>", st["cellh"]),
             Paragraph("<b>Price</b>", st["cellh"]),
             Paragraph("<b>Signal</b>", st["cellh"]),
             Paragraph("<b>Confidence</b>", st["cellh"]),
             Paragraph("<b>RSI</b>", st["cellh"]),
             Paragraph("<b>30d %</b>", st["cellh"]),
             Paragraph("<b>Risk</b>", st["cellh"])]]
    for a in assets:
        sig = a["signal"]
        ind = a["indicators"]
        rows.append([
            Paragraph(f'<b>{a["symbol"]}</b>', st["cell"]),
            Paragraph(f'{ind.get("price","")} {a.get("currency","")}', st["cell"]),
            Paragraph(f'<font color="{SIGNAL_INK.get(sig["signal"], INK).hexval()}"><b>{sig["signal"]}</b></font>', st["cell"]),
            Paragraph(f'{sig["confidence"]}%', st["cell"]),
            Paragraph(str(ind.get("rsi", "—")), st["cell"]),
            Paragraph(_pct(ind.get("change_30d_pct")), st["cell"]),
            Paragraph(str(sig.get("risk_level", "")).capitalize(), st["cell"]),
        ])
    tbl = Table(rows, colWidths=[26 * mm, 28 * mm, 20 * mm, 24 * mm, 18 * mm, 22 * mm, 22 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecfeff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(tbl)

    # Per-asset detail
    for a in assets:
        sig = a["signal"]
        ind = a["indicators"]
        s = sig["signal"]
        flow.append(Paragraph(f'{a["symbol"]} — {a.get("name","")}', st["h3"]))
        badge = Table(
            [[Paragraph(f'<b><font color="{SIGNAL_INK[s].hexval()}">{s}</font></b> · '
                        f'{sig["confidence"]}% confidence · {sig.get("time_horizon","")}', st["cell"]),
              _bar(sig["confidence"], SIGNAL_INK[s], width=50 * mm)]],
            colWidths=[110 * mm, 52 * mm],
        )
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SIGNAL_BG[s]),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        flow.append(badge)
        if sig.get("rationale"):
            flow.append(Paragraph(sig["rationale"], st["body"]))

        macd = ind.get("macd", {}) or {}
        boll = ind.get("bollinger", {}) or {}
        flow.append(Paragraph(
            f'<b>RSI:</b> {ind.get("rsi","—")} &nbsp; '
            f'<b>MACD hist:</b> {macd.get("histogram","—")} &nbsp; '
            f'<b>EMA50:</b> {ind.get("ema50","—")} &nbsp; '
            f'<b>EMA200:</b> {ind.get("ema200","—")} &nbsp; '
            f'<b>BB %b:</b> {boll.get("percent_b","—")}', st["meta"]))

        cases = [[
            _case_cell("Bull case", sig.get("bull_case"), "#065f46", "#ecfdf5", st),
            _case_cell("Bear case", sig.get("bear_case"), "#991b1b", "#fef2f2", st),
        ]]
        ct = Table(cases, colWidths=[85 * mm, 85 * mm])
        ct.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        flow.append(ct)

    # Portfolio
    if portfolio:
        flow.append(Paragraph("Portfolio Assessment", st["h2"]))
        rs = int(portfolio.get("risk_score") or 0)
        gauge = Table(
            [[Paragraph(f'<b>Risk score:</b> {rs}/100 ({str(portfolio.get("risk_level","")).capitalize()})', st["cell"])],
             [_bar(rs, colors.HexColor("#dc2626") if rs >= 66 else colors.HexColor("#d97706") if rs >= 33 else colors.HexColor("#16a34a"), width=150 * mm)]],
            colWidths=[150 * mm])
        gauge.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        flow.append(gauge)
        if portfolio.get("summary"):
            flow.append(Paragraph(portfolio["summary"], st["body"]))
        if portfolio.get("diversification"):
            flow.append(Paragraph(f'<b>Diversification:</b> {portfolio["diversification"]}', st["body"]))
        if portfolio.get("recommendations"):
            flow.append(ListFlowable(
                [ListItem(Paragraph(r, st["item"]), leftIndent=8) for r in portfolio["recommendations"]],
                bulletType="bullet", bulletColor=ACCENT))

    # Errors
    if data.get("errors"):
        flow.append(Paragraph("Skipped Symbols", st["h2"]))
        for e in data["errors"]:
            flow.append(Paragraph(f'{e.get("symbol","")}: {e.get("error","")}', st["meta"]))

    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph(
        "Not financial advice. Signals are AI-generated from technical indicators "
        "for educational purposes only — do your own research.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _case_cell(title: str, items: list, ink: str, bg: str, st: dict) -> Table:
    head = Paragraph(f'<b><font color="{ink}">{title}</font></b>', st["cell"])
    body_items = items or ["—"]
    lst = ListFlowable(
        [ListItem(Paragraph(str(x), st["cell"]), leftIndent=6) for x in body_items],
        bulletType="bullet", bulletColor=colors.HexColor(ink))
    t = Table([[head], [lst]], colWidths=[79 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _pct(v) -> str:
    if v is None:
        return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v}%"
