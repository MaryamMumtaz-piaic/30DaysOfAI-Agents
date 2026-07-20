"""Render a real estate investment analysis into a professional PDF report."""

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

ACCENT = colors.HexColor("#0d9488")   # teal-600
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")

REC_BG = {
    "STRONG BUY": colors.HexColor("#15803d"),
    "BUY": colors.HexColor("#16a34a"),
    "HOLD": colors.HexColor("#d97706"),
    "PASS": colors.HexColor("#dc2626"),
}
SCORE_LABELS = {
    "safety": "Safety", "schools": "Schools", "amenities": "Amenities",
    "transit": "Transit", "walkability": "Walkability", "employment": "Employment",
    "affordability": "Affordability", "growth": "Growth",
}


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("T", parent=base["Title"], fontSize=20,
                                 textColor=ACCENT, spaceAfter=4),
        "subtitle": ParagraphStyle("S", parent=base["Normal"], fontSize=10,
                                    textColor=MUTED, spaceAfter=12),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontSize=14,
                             textColor=INK, spaceBefore=16, spaceAfter=6),
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontSize=11,
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
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title="Real Estate Investment Report",
    )
    st = _styles()
    flow: list = []

    prop = data.get("property", {}) or {}
    val = data.get("valuation", {}) or {}
    rental = data.get("rental", {}) or {}
    nb = data.get("neighborhood", {}) or {}
    roi = data.get("roi", {}) or {}
    rep = data.get("report", {}) or {}
    stats = data.get("stats", {}) or {}

    # Header
    flow.append(Paragraph("Real Estate Investment Analysis", st["title"]))
    flow.append(Paragraph(
        f'{_esc(prop.get("address",""))} · {prop.get("beds","?")}bd/{prop.get("baths","?")}ba · '
        f'{prop.get("sqft","?")} sqft', st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Verdict banner
    rec = rep.get("recommendation", "HOLD")
    bg = REC_BG.get(rec, colors.HexColor("#d97706"))
    banner = Table(
        [[Paragraph(f'<b>{_esc(rec)}</b> &nbsp; — &nbsp; deal score {rep.get("deal_score",0)}/100',
                    st["verdict"])]],
        colWidths=[180 * mm],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    flow.append(Spacer(1, 8))
    flow.append(banner)

    # KPI chips
    chips = [
        ("Est. value", _money(stats.get("estimated_value", 0))),
        ("Cash flow/mo", _money(stats.get("monthly_cash_flow", 0))),
        ("Cap rate", f'{stats.get("cap_rate_pct",0)}%'),
        ("Cash-on-cash", f'{stats.get("cash_on_cash_pct",0)}%'),
        ("Neighborhood", f'{stats.get("neighborhood_score",0)}/100'),
    ]
    chip_row = [[Paragraph(f'<b><font color="{ACCENT.hexval()}">{v}</font></b><br/>'
                           f'<font size="7" color="#64748b">{lbl}</font>', st["cell"])
                 for lbl, v in chips]]
    ct = Table(chip_row, colWidths=[36 * mm] * 5)
    ct.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(Spacer(1, 8))
    flow.append(ct)

    # Investment thesis
    if rep.get("thesis"):
        flow.append(Paragraph("Investment Verdict", st["h2"]))
        flow.append(Paragraph(_esc(rep["thesis"]), st["body"]))
        _bullets(flow, st, "Pros", rep.get("pros"))
        _bullets(flow, st, "Cons", rep.get("cons"))
        if rep.get("best_strategy"):
            flow.append(Paragraph(f'<b>Best strategy:</b> {_esc(rep["best_strategy"])}', st["item"]))
        if rep.get("exit_notes"):
            flow.append(Paragraph(f'<b>Exit outlook:</b> {_esc(rep["exit_notes"])}', st["item"]))

    # Valuation
    flow.append(Paragraph("Market Valuation", st["h2"]))
    flow.append(Paragraph(
        f'Estimated value <b>{_money(val.get("estimated_value"))}</b> · '
        f'{_money(val.get("price_per_sqft"))}/sqft · trend: {_esc(val.get("market_trend",""))} '
        f'({val.get("yoy_change_pct",0)}% YoY) · confidence: {_esc(val.get("confidence",""))}',
        st["item"]))
    if val.get("notes"):
        flow.append(Paragraph(_esc(val["notes"]), st["body"]))
    if val.get("comparables"):
        rows = [[Paragraph("<b>Comparable</b>", st["cellh"]),
                 Paragraph("<b>Price</b>", st["cellh"]),
                 Paragraph("<b>Sqft</b>", st["cellh"]),
                 Paragraph("<b>$/sqft</b>", st["cellh"])]]
        for c in val["comparables"]:
            pps = round(c["price"] / c["sqft"], 0) if c.get("sqft") else 0
            rows.append([
                Paragraph(_esc(c.get("desc", "")), st["cell"]),
                Paragraph(_money(c.get("price")), st["cell"]),
                Paragraph(str(c.get("sqft", "")), st["cell"]),
                Paragraph(_money(pps), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[92 * mm, 30 * mm, 28 * mm, 30 * mm], repeatRows=1)
        tbl.setStyle(_grid(ACCENT))
        flow.append(Spacer(1, 4))
        flow.append(tbl)

    # ROI
    flow.append(Paragraph("ROI & Cash Flow", st["h2"]))
    eb = roi.get("expense_breakdown", {}) or {}
    roi_rows = [
        ["Purchase price", _money(roi.get("purchase_price")), "Down payment", _money(roi.get("down_payment"))],
        ["Loan amount", _money(roi.get("loan_amount")), "Closing costs", _money(roi.get("closing_costs"))],
        ["Gross rent/mo", _money(roi.get("gross_monthly_rent")), "Mortgage/mo", _money(roi.get("mortgage_monthly"))],
        ["NOI (annual)", _money(roi.get("noi_annual")), "Op. expenses/yr", _money(roi.get("operating_expenses_annual"))],
        ["Cash flow/mo", _money(roi.get("monthly_cash_flow")), "Cash flow/yr", _money(roi.get("annual_cash_flow"))],
        ["Cap rate", f'{roi.get("cap_rate_pct",0)}%', "Cash-on-cash", f'{roi.get("cash_on_cash_pct",0)}%'],
    ]
    rows = []
    for a, b, c, d in roi_rows:
        rows.append([
            Paragraph(f'<font color="#64748b">{a}</font>', st["cell"]),
            Paragraph(f'<b>{b}</b>', st["cell"]),
            Paragraph(f'<font color="#64748b">{c}</font>', st["cell"]),
            Paragraph(f'<b>{d}</b>', st["cell"]),
        ])
    tbl = Table(rows, colWidths=[42 * mm, 48 * mm, 42 * mm, 48 * mm])
    tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f0fdfa")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(tbl)
    a = roi.get("assumptions", {}) or {}
    flow.append(Paragraph(
        f'Assumes {a.get("down_pct",0)*100 if a.get("down_pct",0)<=1 else a.get("down_pct",0):.0f}% down · '
        f'{a.get("rate_pct",0)}% / {a.get("term_years",0)}yr mortgage · '
        f'{a.get("vacancy_pct",0)}% vacancy · {a.get("mgmt_pct",0)}% mgmt · {a.get("maint_pct",0)}% maintenance.',
        st["meta"]))

    # Rental strategy
    flow.append(Paragraph("Rental Strategy", st["h2"]))
    rows = [[Paragraph("<b>Strategy</b>", st["cellh"]), Paragraph("<b>Monthly income</b>", st["cellh"]),
             Paragraph("<b>Detail</b>", st["cellh"])],
            [Paragraph("Long-term lease", st["cell"]), Paragraph(_money(rental.get("long_term_monthly")), st["cell"]),
             Paragraph("Stable, lower management", st["cell"])],
            [Paragraph("Short-term (Airbnb)", st["cell"]), Paragraph(_money(rental.get("short_term_monthly")), st["cell"]),
             Paragraph(f'{_money(rental.get("short_term_nightly"))}/night · {rental.get("short_term_occupancy_pct",0)}% occupancy', st["cell"])]]
    tbl = Table(rows, colWidths=[42 * mm, 40 * mm, 98 * mm], repeatRows=1)
    tbl.setStyle(_grid(ACCENT))
    flow.append(tbl)
    flow.append(Paragraph(
        f'<b>Recommended:</b> {_esc(rental.get("recommended_strategy",""))}. {_esc(rental.get("notes",""))}',
        st["item"]))

    # Neighborhood
    flow.append(Paragraph(f'Neighborhood — {nb.get("overall_score",0)}/100', st["h2"]))
    if nb.get("summary"):
        flow.append(Paragraph(_esc(nb["summary"]), st["body"]))
    scores = nb.get("scores", {}) or {}
    cells = []
    for key, label in SCORE_LABELS.items():
        cells.append(Paragraph(f'<b>{scores.get(key,0)}</b><br/><font size="7" color="#64748b">{label}</font>', st["cell"]))
    score_row = [cells[i:i + 4] for i in range(0, len(cells), 4)]
    tbl = Table(score_row, colWidths=[45 * mm] * 4)
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(tbl)
    _bullets(flow, st, "Highlights", nb.get("highlights"))
    _bullets(flow, st, "Concerns", nb.get("concerns"))

    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph(
        "Generated by the AI Real Estate Investment Analyzer. Estimates are AI-generated — verify "
        "with local comps and professional advice before investing.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _grid(header_bg, alt: str = "#f0fdfa") -> TableStyle:
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


def _esc(s) -> str:
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
