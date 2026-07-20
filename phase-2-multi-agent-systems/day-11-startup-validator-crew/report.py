"""Render a startup validation packet into a professional VC-style PDF report."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#7c3aed")   # violet-600
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")

SEV_INK = {
    "high": colors.HexColor("#991b1b"),
    "medium": colors.HexColor("#92400e"),
    "low": colors.HexColor("#3f6212"),
}
DECISION_BG = {
    "GO": colors.HexColor("#16a34a"),
    "CONDITIONAL GO": colors.HexColor("#d97706"),
    "NO-GO": colors.HexColor("#dc2626"),
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
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontSize=11.5,
                             textColor=ACCENT, spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("B", parent=base["Normal"], fontSize=10,
                               leading=15, alignment=TA_JUSTIFY, spaceAfter=6),
        "item": ParagraphStyle("I", parent=base["Normal"], fontSize=9.5,
                               leading=14, alignment=TA_LEFT),
        "cell": ParagraphStyle("C", parent=base["Normal"], fontSize=8.5, leading=11),
        "cellh": ParagraphStyle("CH", parent=base["Normal"], fontSize=8.5,
                                leading=11, textColor=colors.white),
        "verdict": ParagraphStyle("V", parent=base["Normal"], fontSize=15,
                                  textColor=colors.white, alignment=TA_CENTER),
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5, textColor=MUTED),
    }


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Startup Validation Report",
    )
    st = _styles()
    flow: list = []

    market = data.get("market", {}) or {}
    comp = data.get("competitors", {}) or {}
    fin = data.get("financials", {}) or {}
    risks = data.get("risks", {}) or {}
    pitch = data.get("pitch", {}) or {}
    verdict = data.get("verdict", {}) or {}
    stats = data.get("stats", {}) or {}

    # Header
    flow.append(Paragraph(pitch.get("tagline") or "Startup Validation Report", st["title"]))
    flow.append(Paragraph(_esc(data.get("idea", "")), st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Verdict banner
    dec = verdict.get("decision", "CONDITIONAL GO")
    bg = DECISION_BG.get(dec, colors.HexColor("#d97706"))
    banner = Table(
        [[Paragraph(f'<b>{_esc(dec)}</b> &nbsp; — &nbsp; {verdict.get("score", 0)}/100', st["verdict"])]],
        colWidths=[178 * mm],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    flow.append(Spacer(1, 8))
    flow.append(banner)

    # Stat chips
    chips = [
        ("TAM", stats.get("tam_label", "—")),
        ("SOM (3yr)", stats.get("som_label", "—")),
        ("Competitors", stats.get("competitors", 0)),
        ("Yr-3 revenue", stats.get("year3_revenue", "—")),
    ]
    chip_row = [[Paragraph(f'<b><font color="{ACCENT.hexval()}">{v}</font></b><br/>'
                           f'<font size="7" color="#64748b">{lbl}</font>', st["cell"])
                 for lbl, v in chips]]
    ct = Table(chip_row, colWidths=[44.5 * mm] * 4)
    ct.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(Spacer(1, 8))
    flow.append(ct)

    # Verdict detail
    if verdict.get("rationale"):
        flow.append(Paragraph("Investment Verdict", st["h2"]))
        flow.append(Paragraph(_esc(verdict["rationale"]), st["body"]))
        _bullets(flow, st, "Strengths", verdict.get("strengths"))
        _bullets(flow, st, "Concerns", verdict.get("concerns"))
        _bullets(flow, st, "Conditions to invest", verdict.get("conditions"))

    # Pitch
    if pitch.get("elevator_pitch"):
        flow.append(Paragraph("Elevator Pitch", st["h2"]))
        flow.append(Paragraph(_esc(pitch["elevator_pitch"]), st["body"]))
        for label, key in (("Problem", "problem"), ("Solution", "solution"), ("Why now", "why_now")):
            if pitch.get(key):
                flow.append(Paragraph(f'<b>{label}:</b> {_esc(pitch[key])}', st["item"]))
                flow.append(Spacer(1, 2))

    # Market
    flow.append(Paragraph("Market Opportunity", st["h2"]))
    if market.get("summary"):
        flow.append(Paragraph(_esc(market["summary"]), st["body"]))
    mkt_rows = [[Paragraph("<b>TAM</b>", st["cellh"]), Paragraph("<b>SAM</b>", st["cellh"]),
                 Paragraph("<b>SOM (3yr)</b>", st["cellh"]), Paragraph("<b>CAGR</b>", st["cellh"])],
                [Paragraph(_esc(market.get("tam_label", "—")), st["cell"]),
                 Paragraph(_esc(market.get("sam_label", "—")), st["cell"]),
                 Paragraph(_esc(market.get("som_label", "—")), st["cell"]),
                 Paragraph(f'{market.get("cagr_pct", 0)}%', st["cell"])]]
    mt = Table(mkt_rows, colWidths=[44.5 * mm] * 4)
    mt.setStyle(_grid(ACCENT))
    flow.append(mt)
    if market.get("target_customer"):
        flow.append(Spacer(1, 4))
        flow.append(Paragraph(f'<b>Target customer:</b> {_esc(market["target_customer"])}', st["item"]))
    _bullets(flow, st, "Tailwinds", market.get("trends"))
    _bullets(flow, st, "Headwinds", market.get("headwinds"))

    # Competitors
    if comp.get("competitors"):
        flow.append(Paragraph("Competitive Landscape", st["h2"]))
        if comp.get("landscape"):
            flow.append(Paragraph(_esc(comp["landscape"]), st["body"]))
        rows = [[Paragraph("<b>Competitor</b>", st["cellh"]),
                 Paragraph("<b>Positioning</b>", st["cellh"]),
                 Paragraph("<b>Strength</b>", st["cellh"]),
                 Paragraph("<b>Weakness</b>", st["cellh"])]]
        for c in comp["competitors"]:
            rows.append([
                Paragraph(f'<b>{_esc(c.get("name",""))}</b>', st["cell"]),
                Paragraph(_esc(c.get("positioning", "")), st["cell"]),
                Paragraph(_esc(c.get("strength", "")), st["cell"]),
                Paragraph(_esc(c.get("weakness", "")), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[34 * mm, 52 * mm, 46 * mm, 46 * mm], repeatRows=1)
        tbl.setStyle(_grid(ACCENT, alt="#f5f3ff"))
        flow.append(tbl)
        if comp.get("differentiation"):
            flow.append(Spacer(1, 4))
            flow.append(Paragraph(f'<b>Our wedge:</b> {_esc(comp["differentiation"])}', st["item"]))
        if comp.get("moat"):
            flow.append(Spacer(1, 2))
            flow.append(Paragraph(f'<b>Potential moat:</b> {_esc(comp["moat"])}', st["item"]))

    # Financials
    if fin.get("projections"):
        flow.append(Paragraph("Financial Projections", st["h2"]))
        if fin.get("revenue_model"):
            flow.append(Paragraph(f'<b>Revenue model:</b> {_esc(fin["revenue_model"])}', st["item"]))
            flow.append(Spacer(1, 4))
        rows = [[Paragraph("<b>Year</b>", st["cellh"]),
                 Paragraph("<b>Customers</b>", st["cellh"]),
                 Paragraph("<b>Revenue</b>", st["cellh"]),
                 Paragraph("<b>Costs</b>", st["cellh"]),
                 Paragraph("<b>Profit</b>", st["cellh"])]]
        for p in fin["projections"]:
            profit = p.get("profit_usd", 0)
            pc = "#16a34a" if profit >= 0 else "#dc2626"
            rows.append([
                Paragraph(f'Y{p.get("year","")}', st["cell"]),
                Paragraph(_fmt_int(p.get("customers", 0)), st["cell"]),
                Paragraph(_money(p.get("revenue_usd", 0)), st["cell"]),
                Paragraph(_money(p.get("costs_usd", 0)), st["cell"]),
                Paragraph(f'<font color="{pc}">{_money(profit)}</font>', st["cell"]),
            ])
        tbl = Table(rows, colWidths=[22 * mm, 40 * mm, 40 * mm, 38 * mm, 38 * mm], repeatRows=1)
        tbl.setStyle(_grid(ACCENT, alt="#f5f3ff"))
        flow.append(tbl)
        meta_bits = []
        if fin.get("seed_ask_label"):
            meta_bits.append(f'Seed ask: {_esc(fin["seed_ask_label"])}')
        if fin.get("break_even"):
            meta_bits.append(f'Break-even: {_esc(fin["break_even"])}')
        if meta_bits:
            flow.append(Spacer(1, 4))
            flow.append(Paragraph(" · ".join(meta_bits), st["item"]))

    # Risks (PESTLE)
    if risks.get("pestle"):
        flow.append(Paragraph("PESTLE Risk Assessment", st["h2"]))
        if risks.get("summary"):
            flow.append(Paragraph(_esc(risks["summary"]), st["body"]))
        rows = [[Paragraph("<b>Category</b>", st["cellh"]),
                 Paragraph("<b>Risk</b>", st["cellh"]),
                 Paragraph("<b>Severity</b>", st["cellh"]),
                 Paragraph("<b>Mitigation</b>", st["cellh"])]]
        for r in risks["pestle"]:
            sev = str(r.get("severity", "")).lower()
            rows.append([
                Paragraph(f'<b>{_esc(r.get("category",""))}</b>', st["cell"]),
                Paragraph(_esc(r.get("risk", "")), st["cell"]),
                Paragraph(f'<font color="{SEV_INK.get(sev, MUTED).hexval()}">{sev}</font>', st["cell"]),
                Paragraph(_esc(r.get("mitigation", "")), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[28 * mm, 58 * mm, 20 * mm, 72 * mm], repeatRows=1)
        tbl.setStyle(_grid(colors.HexColor("#dc2626"), alt="#fef2f2"))
        flow.append(tbl)

    # Pitch deck outline
    if pitch.get("deck_outline"):
        flow.append(Paragraph("Investor Deck Outline", st["h2"]))
        for i, s in enumerate(pitch["deck_outline"], 1):
            if isinstance(s, dict):
                flow.append(Paragraph(
                    f'<b>{i}. {_esc(s.get("slide",""))}</b> — {_esc(s.get("content",""))}', st["item"]))
            else:
                flow.append(Paragraph(f'<b>{i}.</b> {_esc(s)}', st["item"]))
            flow.append(Spacer(1, 2))

    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph("Generated by the AI Startup Validator Crew.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _grid(header_bg, alt: str = "#f8fafc") -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(alt)]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ])


def _bullets(flow: list, st: dict, label: str, items) -> None:
    items = [x for x in (items or []) if x]
    if not items:
        return
    flow.append(Paragraph(label, st["h3"]))
    for it in items:
        flow.append(Paragraph(f'• {_esc(it)}', st["item"]))
        flow.append(Spacer(1, 1))


def _fmt_int(v) -> str:
    try:
        return f"{int(float(v)):,}"
    except (TypeError, ValueError):
        return str(v)


def _money(v) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "$0"
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


def _esc(s) -> str:
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
