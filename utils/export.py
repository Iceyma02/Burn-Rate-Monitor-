"""
utils/export.py — Investor-ready PDF export
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from io import BytesIO
import pandas as pd
from datetime import datetime

# ── Brand colours ─────────────────────────────────────────────────────────────
ACCENT  = colors.HexColor("#00d4aa")
ACCENT2 = colors.HexColor("#3b82f6")
DARK    = colors.HexColor("#08090c")
CARD    = colors.HexColor("#12151d")
MUTED   = colors.HexColor("#8892a4")
WHITE   = colors.white
DANGER  = colors.HexColor("#ef4444")
WARNING = colors.HexColor("#f59e0b")


def generate_pdf(df: pd.DataFrame, kpis: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=16*mm,  bottomMargin=16*mm,
    )

    styles = getSampleStyleSheet()

    H1 = ParagraphStyle("H1", fontSize=22, fontName="Helvetica-Bold",
                         textColor=WHITE,  leading=28, spaceAfter=4)
    H2 = ParagraphStyle("H2", fontSize=13, fontName="Helvetica-Bold",
                         textColor=ACCENT, leading=18, spaceBefore=14, spaceAfter=6)
    BODY = ParagraphStyle("BODY", fontSize=9, fontName="Helvetica",
                           textColor=MUTED,  leading=14)
    MONO = ParagraphStyle("MONO", fontSize=8, fontName="Courier",
                           textColor=WHITE,  leading=12)
    SUB  = ParagraphStyle("SUB",  fontSize=9, fontName="Helvetica",
                           textColor=MUTED,  leading=12)
    RIGHT= ParagraphStyle("RIGHT",fontSize=9, fontName="Helvetica",
                           textColor=MUTED,  alignment=TA_RIGHT)

    latest      = df.iloc[-1]
    prior       = df.iloc[-2]
    mrr_growth  = ((latest["mrr"] - prior["mrr"]) / prior["mrr"] * 100)
    burn_change = ((latest["total_burn"] - prior["total_burn"]) / prior["total_burn"] * 100)

    story = []

    # ── Header block ─────────────────────────────────────────────────────────
    story.append(Paragraph("BURN RATE &amp; RUNWAY MONITOR", H1))
    story.append(Paragraph(
        f"Investor Report  ·  Generated {datetime.now().strftime('%B %d, %Y')}  ·  MA TechHub",
        SUB,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=14))

    # ── KPI summary table ─────────────────────────────────────────────────────
    story.append(Paragraph("KEY METRICS SNAPSHOT", H2))

    kpi_data = [
        ["Metric", "Current", "Prior Month", "Change"],
        ["Monthly Burn",
         f"${latest['total_burn']:,.0f}",
         f"${prior['total_burn']:,.0f}",
         f"{burn_change:+.1f}%"],
        ["MRR",
         f"${latest['mrr']:,.0f}",
         f"${prior['mrr']:,.0f}",
         f"{mrr_growth:+.1f}%"],
        ["Cash Balance",
         f"${latest['cash_balance']:,.0f}",
         f"${prior['cash_balance']:,.0f}",
         ""],
        ["Net Burn",
         f"${latest['net_burn']:,.0f}",
         f"${prior['net_burn']:,.0f}",
         ""],
        ["Runway",
         f"{latest['runway_months']:.1f} months",
         f"{prior['runway_months']:.1f} months",
         ""],
    ]

    ts = TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), CARD),
        ("TEXTCOLOR",   (0,0), (-1,0), ACCENT),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("FONTNAME",    (0,1), (-1,-1), "Courier"),
        ("TEXTCOLOR",   (0,1), (-1,-1), WHITE),
        ("BACKGROUND",  (0,1), (-1,-1), DARK),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [DARK, CARD]),
        ("ALIGN",       (1,0), (-1,-1), "RIGHT"),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#1c2130")),
        ("TOPPADDING",  (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING",(0,0), (-1,-1), 10),
    ])

    # Colour the Change column
    for i, row in enumerate(kpi_data[1:], 1):
        val = row[3]
        if val.startswith("+"):
            ts.add("TEXTCOLOR", (3,i), (3,i), ACCENT)
        elif val.startswith("-"):
            ts.add("TEXTCOLOR", (3,i), (3,i), DANGER)

    col_w = [65*mm, 40*mm, 40*mm, 35*mm]
    t = Table(kpi_data, colWidths=col_w)
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 12))

    # ── Monthly data table ───────────────────────────────────────────────────
    story.append(Paragraph("MONTHLY FINANCIALS (LAST 12 MONTHS)", H2))

    recent = df.tail(12).copy()
    recent["date"] = pd.to_datetime(recent["date"]).dt.strftime("%b %Y")

    table_data = [["Month", "Total Burn", "MRR", "Net Burn", "Cash Balance", "Runway"]]
    for _, row in recent.iterrows():
        table_data.append([
            row["date"],
            f"${row['total_burn']:,.0f}",
            f"${row['mrr']:,.0f}",
            f"${row['net_burn']:,.0f}",
            f"${row['cash_balance']:,.0f}",
            f"{row['runway_months']:.1f} mo",
        ])

    ts2 = TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), CARD),
        ("TEXTCOLOR",   (0,0), (-1,0), ACCENT),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("FONTNAME",    (0,1), (-1,-1), "Courier"),
        ("TEXTCOLOR",   (0,1), (-1,-1), WHITE),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [DARK, CARD]),
        ("ALIGN",       (1,0), (-1,-1), "RIGHT"),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#1c2130")),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING",(0,0), (-1,-1), 8),
    ])

    # Flag danger rows
    for i, row in enumerate(recent.itertuples(), 1):
        if row.runway_months < 6:
            ts2.add("BACKGROUND", (0,i), (-1,i), colors.HexColor("#200a0a"))
            ts2.add("TEXTCOLOR",  (5,i), (5,i),  DANGER)
        elif row.runway_months < 12:
            ts2.add("TEXTCOLOR",  (5,i), (5,i),  WARNING)

    col_w2 = [28*mm, 32*mm, 28*mm, 28*mm, 34*mm, 26*mm]
    t2 = Table(table_data, colWidths=col_w2)
    t2.setStyle(ts2)
    story.append(t2)
    story.append(Spacer(1, 14))

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED, spaceBefore=8))
    story.append(Paragraph(
        "Confidential · Generated by MA TechHub Burn Rate Monitor · matechhub.io",
        RIGHT,
    ))

    doc.build(story)
    return buf.getvalue()
