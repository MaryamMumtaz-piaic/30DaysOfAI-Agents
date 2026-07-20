"""Render an e-commerce operations run into a professional PDF report."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
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

ACCENT = colors.HexColor("#059669")   # emerald-600
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")

STATUS_INK = {
    "out": colors.HexColor("#7f1d1d"),
    "critical": colors.HexColor("#991b1b"),
    "low": colors.HexColor("#92400e"),
    "ok": colors.HexColor("#3f6212"),
}
ACTION_INK = {
    "raise": colors.HexColor("#065f46"),
    "lower": colors.HexColor("#9a3412"),
    "hold": colors.HexColor("#64748b"),
}
SENT_INK = {
    "positive": colors.HexColor("#3f6212"),
    "mixed": colors.HexColor("#92400e"),
    "negative": colors.HexColor("#991b1b"),
}


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("T", parent=base["Title"], fontSize=21,
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
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5, textColor=MUTED),
    }


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title="E-Commerce Operations Report",
    )
    st = _styles()
    flow: list = []

    stats = data.get("stats", {}) or {}
    inv = data.get("inventory", {}) or {}
    pr = data.get("pricing", {}) or {}
    fc = data.get("forecast", {}) or {}
    reviews = data.get("reviews", {}) or {}
    adcopy = data.get("adcopy", {}) or {}

    # Header
    flow.append(Paragraph("E-Commerce Operations Report", st["title"]))
    flow.append(Paragraph(
        f'{stats.get("products",0)} products managed by 5 autonomous agents', st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Stat chips
    chips = [
        ("Reorder alerts", stats.get("reorder_alerts", 0)),
        ("Reprices", stats.get("reprice_count", 0)),
        ("Forecast units", stats.get("forecast_units", 0)),
        ("Forecast rev.", _money(stats.get("forecast_revenue", 0))),
        ("Avg review", f'{stats.get("avg_review_score")}/100' if stats.get("avg_review_score") is not None else "—"),
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

    # Inventory
    flow.append(Paragraph("Inventory Monitor", st["h2"]))
    rows = [[Paragraph("<b>SKU</b>", st["cellh"]), Paragraph("<b>Product</b>", st["cellh"]),
             Paragraph("<b>Stock</b>", st["cellh"]), Paragraph("<b>Wk sales</b>", st["cellh"]),
             Paragraph("<b>Days left</b>", st["cellh"]), Paragraph("<b>Status</b>", st["cellh"]),
             Paragraph("<b>Reorder</b>", st["cellh"])]]
    for it in inv.get("items", []):
        stt = it["status"]
        dl = it["days_of_stock"]
        rows.append([
            Paragraph(_esc(it["sku"]), st["cell"]),
            Paragraph(f'<b>{_esc(it["name"])}</b>', st["cell"]),
            Paragraph(str(it["stock"]), st["cell"]),
            Paragraph(str(it["avg_weekly_sales"]), st["cell"]),
            Paragraph("—" if dl is None else str(dl), st["cell"]),
            Paragraph(f'<font color="{STATUS_INK.get(stt, MUTED).hexval()}">{stt}</font>', st["cell"]),
            Paragraph(f'+{it["reorder_qty"]}' if it["reorder"] else "—", st["cell"]),
        ])
    tbl = Table(rows, colWidths=[20 * mm, 52 * mm, 18 * mm, 22 * mm, 22 * mm, 24 * mm, 22 * mm], repeatRows=1)
    tbl.setStyle(_grid(ACCENT))
    flow.append(tbl)

    # Pricing
    flow.append(Paragraph("Dynamic Pricing", st["h2"]))
    rows = [[Paragraph("<b>Product</b>", st["cellh"]), Paragraph("<b>Price</b>", st["cellh"]),
             Paragraph("<b>Comp.</b>", st["cellh"]), Paragraph("<b>Suggested</b>", st["cellh"]),
             Paragraph("<b>Margin</b>", st["cellh"]), Paragraph("<b>Action</b>", st["cellh"]),
             Paragraph("<b>Reason</b>", st["cellh"])]]
    for it in pr.get("items", []):
        act = it["action"]
        rows.append([
            Paragraph(f'<b>{_esc(it["name"])}</b>', st["cell"]),
            Paragraph(_money(it["price"]), st["cell"]),
            Paragraph(_money(it["competitor_price"]) if it["competitor_price"] else "—", st["cell"]),
            Paragraph(f'{_money(it["suggested_price"])}', st["cell"]),
            Paragraph(f'{it["margin_pct"]}%→{it["new_margin_pct"]}%', st["cell"]),
            Paragraph(f'<font color="{ACTION_INK.get(act, MUTED).hexval()}">{act}</font>', st["cell"]),
            Paragraph(_esc(it["reason"]), st["cell"]),
        ])
    tbl = Table(rows, colWidths=[38 * mm, 18 * mm, 18 * mm, 22 * mm, 24 * mm, 16 * mm, 44 * mm], repeatRows=1)
    tbl.setStyle(_grid(ACCENT))
    flow.append(tbl)

    # Forecast
    flow.append(Paragraph("Sales Forecast (next period)", st["h2"]))
    rows = [[Paragraph("<b>Product</b>", st["cellh"]), Paragraph("<b>Avg/wk</b>", st["cellh"]),
             Paragraph("<b>Trend</b>", st["cellh"]), Paragraph("<b>Forecast units</b>", st["cellh"]),
             Paragraph("<b>Forecast revenue</b>", st["cellh"])]]
    for it in fc.get("items", []):
        rows.append([
            Paragraph(f'<b>{_esc(it["name"])}</b>', st["cell"]),
            Paragraph(str(it["avg_weekly"]), st["cell"]),
            Paragraph(_esc(it["trend"]), st["cell"]),
            Paragraph(str(it["forecast_units"]), st["cell"]),
            Paragraph(_money(it["forecast_revenue"]), st["cell"]),
        ])
    rows.append([
        Paragraph("<b>Total</b>", st["cell"]), Paragraph("", st["cell"]),
        Paragraph("", st["cell"]), Paragraph(f'<b>{fc.get("total_units",0)}</b>', st["cell"]),
        Paragraph(f'<b>{_money(fc.get("total_revenue",0))}</b>', st["cell"]),
    ])
    tbl = Table(rows, colWidths=[60 * mm, 24 * mm, 22 * mm, 34 * mm, 38 * mm], repeatRows=1)
    tbl.setStyle(_grid(ACCENT))
    flow.append(tbl)

    # Reviews
    if reviews.get("products"):
        flow.append(Paragraph("Customer Review Analysis", st["h2"]))
        if reviews.get("overall"):
            flow.append(Paragraph(_esc(reviews["overall"]), st["body"]))
        for it in reviews["products"]:
            sent = str(it.get("sentiment", "")).lower()
            flow.append(Paragraph(
                f'<b>{_esc(_name(data, it.get("sku")))}</b> — '
                f'<font color="{SENT_INK.get(sent, MUTED).hexval()}">{sent}</font> '
                f'({it.get("score",0)}/100)', st["h3"]))
            if it.get("themes"):
                flow.append(Paragraph("Themes: " + _esc(", ".join(it["themes"])), st["item"]))
            if it.get("response_draft"):
                flow.append(Paragraph(f'<b>Reply:</b> {_esc(it["response_draft"])}', st["item"]))
            flow.append(Spacer(1, 3))

    # Ad copy
    if adcopy.get("products"):
        flow.append(Paragraph("Ad Copy", st["h2"]))
        for it in adcopy["products"]:
            flow.append(Paragraph(_esc(_name(data, it.get("sku"))), st["h3"]))
            rows = [[Paragraph("<b>Platform</b>", st["cellh"]), Paragraph("<b>Headline</b>", st["cellh"]),
                     Paragraph("<b>Body</b>", st["cellh"]), Paragraph("<b>CTA</b>", st["cellh"])]]
            for ad in it.get("ads", []):
                rows.append([
                    Paragraph(_esc(ad.get("platform", "")), st["cell"]),
                    Paragraph(f'<b>{_esc(ad.get("headline",""))}</b>', st["cell"]),
                    Paragraph(_esc(ad.get("body", "")), st["cell"]),
                    Paragraph(_esc(ad.get("cta", "")), st["cell"]),
                ])
            tbl = Table(rows, colWidths=[22 * mm, 44 * mm, 76 * mm, 28 * mm], repeatRows=1)
            tbl.setStyle(_grid(ACCENT))
            flow.append(tbl)
            flow.append(Spacer(1, 4))

    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph("Generated by the Autonomous E-Commerce Operations Manager.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _grid(header_bg, alt: str = "#ecfdf5") -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(alt)]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ])


def _name(data: dict, sku) -> str:
    for p in data.get("products", []):
        if p.get("sku") == sku:
            return p.get("name", sku or "")
    return str(sku or "")


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


def _esc(s) -> str:
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
