"""Render a security audit into a professional PDF report."""

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

ACCENT = colors.HexColor("#2563eb")   # blue-600
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")

SEV_INK = {
    "critical": colors.HexColor("#7f1d1d"),
    "high": colors.HexColor("#991b1b"),
    "medium": colors.HexColor("#92400e"),
    "low": colors.HexColor("#1e40af"),
    "info": colors.HexColor("#334155"),
}
SEV_BG = {
    "critical": colors.HexColor("#fee2e2"),
    "high": colors.HexColor("#fef2f2"),
    "medium": colors.HexColor("#fffbeb"),
    "low": colors.HexColor("#eff6ff"),
    "info": colors.HexColor("#f1f5f9"),
}
GRADE_COLOR = {
    "A": colors.HexColor("#16a34a"), "B": colors.HexColor("#65a30d"),
    "C": colors.HexColor("#d97706"), "D": colors.HexColor("#ea580c"),
    "F": colors.HexColor("#dc2626"),
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
        "code": ParagraphStyle("Code", parent=base["Normal"], fontSize=8,
                               leading=11, fontName="Courier",
                               textColor=colors.HexColor("#0f172a")),
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5, textColor=MUTED),
    }


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Security Audit Report",
    )
    st = _styles()
    flow: list = []
    counts = data.get("counts", {}) or {}
    findings = data.get("findings", [])
    grade = data.get("grade", "?")

    # Header
    flow.append(Paragraph("Security Audit Report", st["title"]))
    flow.append(Paragraph(
        f"{'URL' if data.get('mode')=='url' else 'Code'} audit  ·  target: {_esc(data.get('target',''))}",
        st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Grade + risk score
    gcolor = GRADE_COLOR.get(grade, MUTED)
    header = Table(
        [[Paragraph(f'<font size="34" color="{gcolor.hexval()}"><b>{grade}</b></font>', st["cell"]),
          Paragraph(f'<b>Risk score:</b> {data.get("risk_score",0)}/100<br/>'
                    f'<b>Total findings:</b> {data.get("total",0)}', st["cell"])]],
        colWidths=[30 * mm, 140 * mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(Spacer(1, 4))
    flow.append(header)

    # Severity chips
    chips = [("Critical", counts.get("critical", 0)), ("High", counts.get("high", 0)),
             ("Medium", counts.get("medium", 0)), ("Low", counts.get("low", 0)),
             ("Info", counts.get("info", 0))]
    chip_row = [[Paragraph(
        f'<b><font color="{SEV_INK[lbl.lower()].hexval()}">{v}</font></b><br/>'
        f'<font size="7" color="#64748b">{lbl}</font>', st["cell"]) for lbl, v in chips]]
    ct = Table(chip_row, colWidths=[34 * mm] * 5)
    ct.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(Spacer(1, 6))
    flow.append(ct)

    if data.get("summary"):
        flow.append(Paragraph("Executive Summary", st["h2"]))
        flow.append(Paragraph(_esc(data["summary"]), st["body"]))

    # Findings
    if findings:
        flow.append(Paragraph("Findings", st["h2"]))
        for i, f in enumerate(findings, 1):
            sev = f["severity"]
            ink = SEV_INK.get(sev, MUTED)
            inner: list = [Paragraph(
                f'<b>{i}. {_esc(f.get("title",""))}</b> '
                f'<font color="{ink.hexval()}" size="8"><b>[{sev.upper()}]</b></font> '
                f'<font size="8" color="#64748b">{_esc(f.get("category",""))}'
                + (f' · {_esc(f.get("cwe",""))}' if f.get("cwe") else "")
                + (f' · line {f.get("line")}' if f.get("line") else "") + '</font>', st["cell"])]
            if f.get("detail"):
                inner.append(Paragraph(_esc(f["detail"]), st["cell"]))
            if f.get("fix"):
                inner.append(Paragraph(f'<b>Fix:</b> {_esc(f["fix"])}', st["cell"]))
            if f.get("fix_code"):
                inner.append(Spacer(1, 2))
                inner.append(Paragraph(_esc(f["fix_code"]).replace("\n", "<br/>"), st["code"]))
            box = Table([[inner]], colWidths=[170 * mm])
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), SEV_BG.get(sev, colors.white)),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, ink),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            flow.append(box)
            flow.append(Spacer(1, 4))
    else:
        flow.append(Paragraph("No issues detected in this scan.", st["body"]))

    # Remediation roadmap
    recs = data.get("recommendations", [])
    if recs:
        flow.append(Paragraph("Remediation Roadmap", st["h2"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(_esc(str(r)), st["item"]), leftIndent=8) for r in recs],
            bulletType="1", bulletColor=ACCENT))

    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph(
        "Automated defensive security audit for authorized testing and educational use only. "
        "Findings should be verified by a qualified security professional.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _esc(s) -> str:
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
