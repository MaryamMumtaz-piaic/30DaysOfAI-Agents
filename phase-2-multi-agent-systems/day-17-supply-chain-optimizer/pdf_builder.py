"""ReportLab PDF report builder for the AI Supply Chain Risk & Optimizer System.

Generates an executive supply chain optimization report containing:
  - Cover page with product metadata and executive dashboard summary
  - Supplier Risk Assessment table (with colored risk tags)
  - Logistics Route & Lead Time optimization report
  - Sourcing Cost Savings analysis
  - Inventory Reorder & Demand Forecast guidelines
  - Disruption Alerts & Geopolitical Warnings bulletin
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import KeepTogether

# ---------------------------------------------------------------------------
# Color palette (Light Theme Professional Colors)
# ---------------------------------------------------------------------------
NAVY = colors.HexColor("#0F172A")       # Primary text & dark headers
INDIGO = colors.HexColor("#4F46E5")     # Primary brand accent
SLATE = colors.HexColor("#64748B")      # Secondary text
LIGHT_BG = colors.HexColor("#F8FAFC")   # Table background
BORDER = colors.HexColor("#E2E8F0")     # Light divider borders

RED_RISK = colors.HexColor("#EF4444")   # High risk
YEL_RISK = colors.HexColor("#F59E0B")   # Med risk
GRN_RISK = colors.HexColor("#10B981")   # Low risk

def get_risk_color(level: str) -> colors.Color:
    lvl = str(level).strip().lower()
    if "high" in lvl:
        return RED_RISK
    if "med" in lvl:
        return YEL_RISK
    return GRN_RISK

# ---------------------------------------------------------------------------
# Style builder
# ---------------------------------------------------------------------------
def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=INDIGO,
            alignment=TA_CENTER,
            spaceAfter=15,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=SLATE,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=NAVY,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "subsection_heading": ParagraphStyle(
            "subsection_heading",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=INDIGO,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=colors.HexColor("#334155"),
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "body_justify": ParagraphStyle(
            "body_justify",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=colors.HexColor("#334155"),
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "table_text": ParagraphStyle(
            "table_text",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=colors.HexColor("#1E293B"),
            alignment=TA_LEFT,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        "alert_text": ParagraphStyle(
            "alert_text",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=4,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=SLATE,
            alignment=TA_CENTER,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=INDIGO,
            alignment=TA_CENTER,
        )
    }

# ---------------------------------------------------------------------------
# PDF Generation main function
# ---------------------------------------------------------------------------
def build_supply_chain_pdf(report: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    s = _styles()
    story: list[Any] = []

    # 1. Header & Cover Section
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("MARSA EMPOWER — SUPPLY CHAIN INTELLIGENCE", s["cover_sub"]))
    story.append(Paragraph("Logistics Network Optimization Report", s["cover_title"]))
    story.append(HRFlowable(width="100%", thickness=2, color=INDIGO, spaceBefore=4, spaceAfter=8))
    
    prod_name = report.get("metadata", {}).get("product_name", "Supply Chain Portfolio")
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    model_name = report.get("metadata", {}).get("agent_model", "Marsa AI Agent Group")
    
    story.append(Paragraph(f"<b>Target Product/BOM:</b> {prod_name}", s["cover_meta"]))
    story.append(Paragraph(f"<b>Generated On:</b> {gen_time} (Local Time)", s["cover_meta"]))
    story.append(Paragraph(f"<b>Optimization Engine:</b> {model_name}", s["cover_meta"]))
    story.append(Spacer(1, 10 * mm))

    # 2. Executive Dashboard (KPI Grid)
    story.append(Paragraph("Executive Optimization Summary", s["section_heading"]))
    
    risk_summary = report.get("metadata", {}).get("risk_summary", {})
    log_summary = report.get("metadata", {}).get("logistics_summary", {})
    fin_summary = report.get("metadata", {}).get("financial_summary", {})
    
    kpi_data = [
        [
            Paragraph("<b>Overall Risk Index</b>", s["kpi_label"]),
            Paragraph("<b>Logistics Transit Savings</b>", s["kpi_label"]),
            Paragraph("<b>Estimated BOM Savings</b>", s["kpi_label"])
        ],
        [
            Paragraph(f"{risk_summary.get('average_score', 0)} / 100", s["kpi_value"]),
            Paragraph(f"-{log_summary.get('savings_days', 0)} Days", s["kpi_value"]),
            Paragraph(f"${fin_summary.get('potential_savings', 0):,.2f}", s["kpi_value"])
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('BOX', (0, 0), (-1, -1), 1, INDIGO),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 8 * mm))

    # 3. Section: Supplier Risk Assessment
    story.append(Paragraph("1. Supplier Risk Matrix & Assessment", s["section_heading"]))
    story.append(Paragraph(
        "This section evaluates geopolitical factors, financial stability, and ESG compliance. "
        "Critical risks require alternate supplier contract routing or geographical shifts.",
        s["body"]
    ))
    
    risk_headers = ["Component", "Supplier", "Origin", "Geopolitical", "ESG", "Risk Score", "Risk Level"]
    risk_table_data = [[Paragraph(f"<b>{h}</b>", s["table_header"]) for h in risk_headers]]
    
    for r in report.get("risk_analysis", []):
        r_level = r.get("risk_level", "Low")
        r_color_hex = "#10B981" if r_level == "Low" else ("#F59E0B" if r_level == "Medium" else "#EF4444")
        
        row = [
            Paragraph(r.get("component", ""), s["table_text"]),
            Paragraph(r.get("supplier", ""), s["table_text"]),
            Paragraph(r.get("origin", ""), s["table_text"]),
            Paragraph(r.get("geopolitical_risk", ""), s["table_text"]),
            Paragraph(r.get("esg_score", ""), s["table_text"]),
            Paragraph(str(r.get("risk_score", 0)), s["table_text"]),
            Paragraph(f"<font color='{r_color_hex}'><b>{r_level}</b></font>", s["table_text"])
        ]
        risk_table_data.append(row)
        
    risk_table = Table(risk_table_data, colWidths=[30*mm, 28*mm, 28*mm, 24*mm, 15*mm, 22*mm, 33*mm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), INDIGO),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 8 * mm))

    # 4. Section: Logistics & Routing Optimization
    story.append(Paragraph("2. Sourcing Routes & Lead Time Optimization", s["section_heading"]))
    story.append(Paragraph(
        "Analysis of transit operations. Recommends routing modifications to avoid port congestion "
        "and custom clearance bottlenecks. Target destination: Marsa Assembly Hub (Karachi, Pakistan).",
        s["body"]
    ))
    
    route_headers = ["Component", "Supplier", "Origin", "Ship Mode", "Original (Days)", "Optimized (Days)", "Optimization Saving"]
    route_table_data = [[Paragraph(f"<b>{h}</b>", s["table_header"]) for h in route_headers]]
    
    routing = report.get("routing_optimization", {})
    for rt in routing.get("routes", []):
        orig_lt = rt.get("original_lead_time", 0)
        opt_lt = rt.get("optimized_lead_time", 0)
        diff = orig_lt - opt_lt
        
        row = [
            Paragraph(rt.get("component", ""), s["table_text"]),
            Paragraph(rt.get("supplier", ""), s["table_text"]),
            Paragraph(rt.get("origin", ""), s["table_text"]),
            Paragraph(rt.get("mode", ""), s["table_text"]),
            Paragraph(str(orig_lt), s["table_text"]),
            Paragraph(str(opt_lt), s["table_text"]),
            Paragraph(f"<font color='#10B981'><b>-{diff} Days</b></font>" if diff > 0 else "0", s["table_text"])
        ]
        route_table_data.append(row)
        
    route_table = Table(route_table_data, colWidths=[32*mm, 28*mm, 28*mm, 20*mm, 24*mm, 24*mm, 24*mm])
    route_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(route_table)
    story.append(Spacer(1, 5 * mm))

    # Add Bottleneck alert sub-section if any
    bottlenecks = routing.get("bottlenecks", [])
    if bottlenecks:
        story.append(Paragraph("Identified Supply Chain Bottlenecks", s["subsection_heading"]))
        for b in bottlenecks:
            story.append(Paragraph(
                f"⚠️ <b>{b.get('component')}</b> (Origin: {b.get('origin')}, Lead Time: {b.get('current_time')} Days): {b.get('reason')}",
                s["alert_text"]
            ))
        story.append(Spacer(1, 5 * mm))

    story.append(PageBreak())

    # 5. Section: Cost Reduction Recommendations
    story.append(Paragraph("3. Sourcing Cost Sparing & Alternative Suppliers", s["section_heading"]))
    story.append(Paragraph(
        "Suggested actions for strategic cost reduction. Recommends local alternatives, "
        "domestic substitution, and supply-contract restructuring.",
        s["body"]
    ))
    
    cost_headers = ["Component", "Current Supplier (Cost)", "Alternative Sourcing", "Alternative Cost", "Est. Savings", "Strategic Recommendation"]
    cost_table_data = [[Paragraph(f"<b>{h}</b>", s["table_header"]) for h in cost_headers]]
    
    cost_opt = report.get("cost_reduction", {})
    for c in cost_opt.get("suggestions", []):
        row = [
            Paragraph(c.get("component", ""), s["table_text"]),
            Paragraph(f"{c.get('current_supplier', '')}<br/>(${c.get('current_cost', 0):.2f})", s["table_text"]),
            Paragraph(c.get("alternative_supplier", ""), s["table_text"]),
            Paragraph(f"${c.get('alternative_cost', 0):.2f}", s["table_text"]),
            Paragraph(f"<b>{c.get('estimated_savings_percentage', 0)}%</b>", s["table_text"]),
            Paragraph(c.get("recommendation", ""), s["table_text"])
        ]
        cost_table_data.append(row)
        
    cost_table = Table(cost_table_data, colWidths=[28*mm, 32*mm, 32*mm, 24*mm, 20*mm, 44*mm])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), INDIGO),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(cost_table)
    story.append(Spacer(1, 8 * mm))

    # 6. Section: Demand Forecasting & Safety Stock
    story.append(Paragraph("4. Material Demand Forecasting & Reorder Logic", s["section_heading"]))
    story.append(Paragraph(
        "Calculated safety stock buffers and reorder trigger levels. Reorder point (ROP) indicates "
        "when procurement teams should place component replenishment orders to prevent stockouts.",
        s["body"]
    ))
    
    reorder_headers = ["Component", "Daily Usage Rate (Units)", "Lead Time (Days)", "Safety Stock (Units)", "Reorder Point (Units)", "Stockout Risk"]
    reorder_table_data = [[Paragraph(f"<b>{h}</b>", s["table_header"]) for h in reorder_headers]]
    
    demand = report.get("demand_forecast", {})
    for rl in demand.get("reorder_logic", []):
        risk = rl.get("stockout_risk_level", "Low")
        risk_col = "#EF4444" if "High" in risk else ("#F59E0B" if "Med" in risk else "#10B981")
        row = [
            Paragraph(rl.get("component", ""), s["table_text"]),
            Paragraph(str(rl.get("daily_demand", 0)), s["table_text"]),
            Paragraph(str(rl.get("lead_time_days", 0)), s["table_text"]),
            Paragraph(f"{rl.get('recommended_safety_stock_units', 0):,}", s["table_text"]),
            Paragraph(f"<b>{rl.get('reorder_point_units', 0):,}</b>", s["table_text"]),
            Paragraph(f"<font color='{risk_col}'><b>{risk}</b></font>", s["table_text"])
        ]
        reorder_table_data.append(row)
        
    reorder_table = Table(reorder_table_data, colWidths=[35*mm, 35*mm, 26*mm, 28*mm, 30*mm, 26*mm])
    reorder_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(reorder_table)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(f"<b>Procurement Strategy Notes:</b> {demand.get('forecasting_notes', '')}", s["body"]))
    story.append(Spacer(1, 8 * mm))

    # 7. Section: News-Based Disruption Bulletin
    story.append(Paragraph("5. Active Logistics Network Disruption Alerts", s["section_heading"]))
    story.append(Paragraph(
        "Current geopolitical, climatic, and industrial labor issues that threaten shipments to Karachi.",
        s["body"]
    ))
    
    alerts = report.get("disruption_alerts", [])
    if alerts:
        for a in alerts:
            al_color = "#EF4444" if "High" in a.get("impact", "") else ("#F59E0B" if "Med" in a.get("impact", "") else "#10B981")
            alert_box_data = [
                [
                    Paragraph(f"🚨 <b>{a.get('title')}</b> - <i>{a.get('location')}</i>", ParagraphStyle("sub", parent=s["subsection_heading"], spaceBefore=0)),
                    Paragraph(f"<font color='{al_color}'><b>{a.get('impact')} Impact</b></font>", ParagraphStyle("imp", parent=s["table_text"], alignment=TA_RIGHT))
                ],
                [
                    Paragraph(f"<b>Category:</b> {a.get('category')} | <b>Details:</b> {a.get('details')}", s["body"]),
                    ""
                ]
            ]
            alert_box = Table(alert_box_data, colWidths=[130 * mm, 50 * mm])
            alert_box.setStyle(TableStyle([
                ('SPAN', (0, 1), (1, 1)),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFBEB") if "High" in a.get("impact", "") or "Medium" in a.get("impact", "") else LIGHT_BG),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#FCD34D") if "High" in a.get("impact", "") or "Medium" in a.get("impact", "") else BORDER),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(alert_box)
            story.append(Spacer(1, 3 * mm))
    else:
        story.append(Paragraph("✅ No active maritime, weather, or custom issues detected on current sourcing corridors.", s["body"]))
        
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceBefore=4, spaceAfter=8))
    
    # Sign-off footer
    story.append(Paragraph("Report issued by <b>Marsa Empower Sourcing & AI Command Hub</b>.", s["cover_meta"]))
    story.append(Paragraph("For inquiries contact Maryam Mumtaz, AI Agent Engineer. Web: maryam-piaic.vercel.app", s["cover_meta"]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
