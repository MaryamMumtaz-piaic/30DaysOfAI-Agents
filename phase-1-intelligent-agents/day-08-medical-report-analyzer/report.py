"""Render a medical report analysis into a patient-friendly PDF."""

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

ACCENT = colors.HexColor("#0d9488")   # teal-600
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")

STATUS_INK = {
    "normal": colors.HexColor("#065f46"),
    "borderline": colors.HexColor("#92400e"),
    "critical": colors.HexColor("#991b1b"),
}
STATUS_BG = {
    "normal": colors.HexColor("#ecfdf5"),
    "borderline": colors.HexColor("#fffbeb"),
    "critical": colors.HexColor("#fef2f2"),
}
SEV_INK = {
    "low": colors.HexColor("#3f6212"),
    "medium": colors.HexColor("#92400e"),
    "high": colors.HexColor("#991b1b"),
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
        "body": ParagraphStyle("B", parent=base["Normal"], fontSize=10,
                               leading=15, alignment=TA_JUSTIFY, spaceAfter=6),
        "item": ParagraphStyle("I", parent=base["Normal"], fontSize=9.5,
                               leading=14, alignment=TA_LEFT),
        "cell": ParagraphStyle("C", parent=base["Normal"], fontSize=9, leading=12),
        "cellh": ParagraphStyle("CH", parent=base["Normal"], fontSize=9,
                                leading=12, textColor=colors.white),
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5, textColor=MUTED),
    }


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Medical Report Analysis",
    )
    st = _styles()
    flow: list = []
    stats = data.get("stats", {}) or {}
    markers = data.get("markers", [])
    overall = str(data.get("overall_status", "normal")).lower()

    # Header
    flow.append(Paragraph("Medical Report Analysis", st["title"]))
    flow.append(Paragraph(
        f"{data.get('report_type','Report')}  ·  overall status: "
        f"{overall.capitalize()}", st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Urgent banner
    if data.get("urgent") and data.get("urgent_note"):
        banner = Table([[Paragraph(
            f'<b>⚠ Seek prompt medical attention:</b> {data["urgent_note"]}', st["cell"])]],
            colWidths=[170 * mm])
        banner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#dc2626")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        flow.append(Spacer(1, 4))
        flow.append(banner)

    # Stat chips
    chips = [
        ("Markers", stats.get("total", 0), "#334155"),
        ("Normal", stats.get("normal", 0), "#16a34a"),
        ("Borderline", stats.get("borderline", 0), "#d97706"),
        ("Critical", stats.get("critical", 0), "#dc2626"),
    ]
    chip_row = [[Paragraph(f'<b><font color="{c}">{v}</font></b><br/>'
                           f'<font size="7" color="#64748b">{lbl}</font>', st["cell"])
                 for lbl, v, c in chips]]
    ct = Table(chip_row, colWidths=[42 * mm] * len(chips))
    ct.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(Spacer(1, 6))
    flow.append(ct)

    # Summary
    if data.get("patient_summary"):
        flow.append(Paragraph("What This Means", st["h2"]))
        flow.append(Paragraph(data["patient_summary"], st["body"]))

    # Markers table
    if markers:
        flow.append(Paragraph("Marker-by-Marker Results", st["h2"]))
        rows = [[Paragraph("<b>Marker</b>", st["cellh"]),
                 Paragraph("<b>Value</b>", st["cellh"]),
                 Paragraph("<b>Reference</b>", st["cellh"]),
                 Paragraph("<b>Status</b>", st["cellh"]),
                 Paragraph("<b>What it means</b>", st["cellh"])]]
        for m in markers:
            status = m["status"]
            ink = STATUS_INK.get(status, INK)
            arrow = {"low": " ↓", "high": " ↑"}.get(str(m.get("direction", "")).lower(), "")
            rows.append([
                Paragraph(f'<b>{_esc(m.get("name",""))}</b>', st["cell"]),
                Paragraph(f'{_esc(m.get("value",""))} {_esc(m.get("unit",""))}', st["cell"]),
                Paragraph(_esc(m.get("reference_range", "")), st["cell"]),
                Paragraph(f'<font color="{ink.hexval()}"><b>{status}{arrow}</b></font>', st["cell"]),
                Paragraph(_esc(m.get("explanation", "")), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[32 * mm, 24 * mm, 26 * mm, 24 * mm, 64 * mm], repeatRows=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]
        # Tint each data row by status.
        for i, m in enumerate(markers, 1):
            style.append(("BACKGROUND", (0, i), (-1, i), STATUS_BG.get(m["status"], colors.white)))
        tbl.setStyle(TableStyle(style))
        flow.append(tbl)

    # Risks
    risks = data.get("risks", [])
    if risks:
        flow.append(Paragraph("Potential Health Risks", st["h2"]))
        for r in risks:
            sev = str(r.get("severity", "low")).lower()
            based = ", ".join(r.get("based_on", []) or [])
            flow.append(Paragraph(
                f'<b><font color="{SEV_INK.get(sev, INK).hexval()}">[{sev.upper()}]</font></b> '
                f'{_esc(r.get("risk",""))}'
                + (f' <font size="8" color="#64748b">(based on: {_esc(based)})</font>' if based else ""),
                st["item"]))
            flow.append(Spacer(1, 3))

    # Recommendations
    if data.get("recommendations"):
        flow.append(Paragraph("Recommended Next Steps", st["h2"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(_esc(r), st["item"]), leftIndent=8) for r in data["recommendations"]],
            bulletType="bullet", bulletColor=ACCENT))

    # Disclaimer
    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph(
        "This analysis is generated by AI for educational purposes only and is NOT a "
        "medical diagnosis. Always consult a qualified healthcare professional about your results.",
        st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _esc(s) -> str:
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
