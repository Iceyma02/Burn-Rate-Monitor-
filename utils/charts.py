"""
utils/charts.py — Plotly chart factory for Burn Rate Monitor
All charts share a unified dark theme with MA TechHub brand colours.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots

# ── Palette ───────────────────────────────────────────────────────────────────
ACCENT   = "#00d4aa"
ACCENT2  = "#3b82f6"
ACCENT3  = "#f59e0b"
DANGER   = "#ef4444"
SUCCESS  = "#10b981"
MUTED    = "#4a5568"
TEXT_PRI = "#e8eaf0"
TEXT_SEC = "#8892a4"
BG_CARD  = "#12151d"
BG_DEEP  = "#0d0f14"
BORDER   = "rgba(255,255,255,0.06)"

LAYOUT_BASE = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font          = dict(family="'Syne', sans-serif", color=TEXT_SEC, size=11),
    margin        = dict(l=0, r=0, t=8, b=0),
    showlegend    = False,
    hoverlabel    = dict(
        bgcolor    = "#1c2130",
        bordercolor= BORDER,
        font_family= "'DM Mono', monospace",
        font_size  = 11,
        font_color = TEXT_PRI,
    ),
    xaxis = dict(
        gridcolor     = "rgba(255,255,255,0.04)",
        linecolor     = BORDER,
        tickcolor     = BORDER,
        tickfont      = dict(family="'DM Mono', monospace", size=10),
        zeroline      = False,
    ),
    yaxis = dict(
        gridcolor     = "rgba(255,255,255,0.04)",
        linecolor     = BORDER,
        tickcolor     = BORDER,
        tickfont      = dict(family="'DM Mono', monospace", size=10),
        zeroline      = False,
    ),
)

def _layout(**kwargs):
    base = dict(**LAYOUT_BASE)
    # deep copy nested
    base["xaxis"] = dict(**LAYOUT_BASE["xaxis"])
    base["yaxis"] = dict(**LAYOUT_BASE["yaxis"])
    base.update(kwargs)
    return base


# ── 1. Cash Balance Area Chart ────────────────────────────────────────────────
def cash_balance_chart(df: pd.DataFrame, scenario_cash: list = None) -> go.Figure:
    dates = pd.to_datetime(df["date"])

    fig = go.Figure()

    # Danger zone fill below $100k
    danger_y = [min(row, 100000) for row in df["cash_balance"]]
    fig.add_trace(go.Scatter(
        x=dates, y=danger_y,
        fill="tozeroy", fillcolor="rgba(239,68,68,0.06)",
        line=dict(width=0), showlegend=False,
        hoverinfo="skip",
    ))

    # Main area
    fig.add_trace(go.Scatter(
        x=dates, y=df["cash_balance"],
        fill="tozeroy",
        fillcolor="rgba(0,212,170,0.07)",
        line=dict(color=ACCENT, width=2.5),
        name="Cash Balance",
        hovertemplate="<b>%{x|%b %Y}</b><br>Cash: $%{y:,.0f}<extra></extra>",
        mode="lines",
    ))

    # Scenario overlay
    if scenario_cash:
        fig.add_trace(go.Scatter(
            x=dates, y=scenario_cash,
            line=dict(color=ACCENT2, width=2, dash="dot"),
            name="Scenario",
            hovertemplate="<b>Scenario</b>: $%{y:,.0f}<extra></extra>",
            mode="lines",
        ))

    # Zero line
    fig.add_hline(y=0, line_color=DANGER, line_width=1, line_dash="dash",
                  annotation_text="Zero cash", annotation_font_color=DANGER,
                  annotation_font_size=9)

    # $100k warning line
    fig.add_hline(y=100000, line_color=ACCENT3, line_width=1, line_dash="dot",
                  annotation_text="$100k warning", annotation_font_color=ACCENT3,
                  annotation_font_size=9)

    layout = _layout(height=260)
    layout["yaxis"]["tickprefix"] = "$"
    layout["yaxis"]["tickformat"] = ",.0s"
    fig.update_layout(**layout)
    return fig


# ── 2. Burn Breakdown Stacked Bar ─────────────────────────────────────────────
def burn_breakdown_chart(df: pd.DataFrame) -> go.Figure:
    dates  = pd.to_datetime(df["date"])
    cats   = ["salaries", "infrastructure", "marketing", "software", "office", "misc"]
    colors = [ACCENT, ACCENT2, ACCENT3, "#8b5cf6", "#ec4899", MUTED]
    labels = ["Salaries", "Infrastructure", "Marketing", "Software", "Office", "Misc"]

    fig = go.Figure()
    for cat, color, label in zip(cats, colors, labels):
        fig.add_trace(go.Bar(
            x=dates, y=df[cat],
            name=label,
            marker_color=color,
            marker_opacity=0.85,
            hovertemplate=f"<b>{label}</b>: $%{{y:,.0f}}<extra></extra>",
        ))

    layout = _layout(height=250)
    layout["showlegend"] = True
    layout["barmode"] = "stack"
    layout["legend"] = dict(
        orientation="h", y=-0.22, x=0,
        font=dict(family="'DM Mono', monospace", size=9, color=TEXT_SEC),
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(**layout)
    fig.update_yaxes(tickprefix="$", tickformat=",.0s")
    return fig


# ── 3. MRR Growth Line ────────────────────────────────────────────────────────
def mrr_chart(df: pd.DataFrame) -> go.Figure:
    dates = pd.to_datetime(df["date"])

    fig = go.Figure()

    # MRR area
    fig.add_trace(go.Scatter(
        x=dates, y=df["mrr"],
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.08)",
        line=dict(color=ACCENT2, width=2.5),
        name="MRR",
        hovertemplate="<b>%{x|%b %Y}</b><br>MRR: $%{y:,.0f}<extra></extra>",
    ))

    # Net burn overlay
    fig.add_trace(go.Scatter(
        x=dates, y=df["net_burn"],
        line=dict(color=DANGER, width=1.5, dash="dot"),
        name="Net Burn",
        hovertemplate="Net Burn: $%{y:,.0f}<extra></extra>",
    ))

    layout = _layout(height=260)
    layout["showlegend"] = True
    layout["legend"] = dict(
        orientation="h", y=-0.22, x=0,
        font=dict(family="'DM Mono', monospace", size=9, color=TEXT_SEC),
        bgcolor="rgba(0,0,0,0)",
    )
    layout["yaxis"]["tickprefix"] = "$"
    layout["yaxis"]["tickformat"] = ",.0s"
    fig.update_layout(**layout)
    return fig


# ── 4. Runway Gauge ───────────────────────────────────────────────────────────
def runway_gauge(months_left: float) -> go.Figure:
    months_left = max(0, min(float(months_left), 36))
    color = ACCENT if months_left >= 12 else ACCENT3 if months_left >= 6 else DANGER

    fig = go.Figure(go.Indicator(
        mode   = "gauge+number",
        value  = months_left,
        number = dict(
            suffix    = " mo",
            font      = dict(family="'Syne', sans-serif", size=36, color=color),
            valueformat = ".1f",
        ),
        gauge  = dict(
            axis    = dict(
                range=[0, 36],
                tickwidth=1,
                tickcolor=BORDER,
                tickfont=dict(family="'DM Mono', monospace", size=9, color=TEXT_SEC),
                nticks=7,
            ),
            bar     = dict(color=color, thickness=0.22),
            bgcolor = "rgba(0,0,0,0)",
            borderwidth=0,
            steps   = [
                dict(range=[0, 6],   color="rgba(239,68,68,0.12)"),
                dict(range=[6, 12],  color="rgba(245,158,11,0.08)"),
                dict(range=[12, 36], color="rgba(0,212,170,0.06)"),
            ],
            threshold=dict(
                line=dict(color=ACCENT3, width=2),
                value=12,
            ),
        ),
    ))

    fig.update_layout(
        height=220,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=0),
        font=dict(family="'Syne', sans-serif", color=TEXT_SEC),
    )
    return fig


# ── 5. CAC / LTV Scatter ──────────────────────────────────────────────────────
def cac_ltv_chart(df: pd.DataFrame) -> go.Figure:
    # Synthetic per-cohort CAC and LTV
    np.random.seed(7)
    n = len(df)
    cac = [1200 + i*40 + np.random.randint(-200, 200) for i in range(n)]
    ltv = [c * np.random.uniform(2.5, 5.5) for c in cac]
    ratio = [l/c for l, c in zip(ltv, cac)]
    colors_val = [ACCENT if r >= 3 else ACCENT3 if r >= 2 else DANGER for r in ratio]

    fig = go.Figure(go.Scatter(
        x=cac, y=ltv,
        mode="markers",
        marker=dict(
            color=colors_val,
            size=8,
            opacity=0.8,
            line=dict(width=0),
        ),
        hovertemplate="<b>CAC:</b> $%{x:,.0f}<br><b>LTV:</b> $%{y:,.0f}<extra></extra>",
    ))

    # 3:1 line
    max_cac = max(cac)
    fig.add_trace(go.Scatter(
        x=[0, max_cac], y=[0, max_cac * 3],
        mode="lines",
        line=dict(color=ACCENT, width=1, dash="dash"),
        hoverinfo="skip",
    ))

    layout = _layout(height=220)
    layout["xaxis"]["title"] = dict(text="CAC ($)", font=dict(size=10, color=TEXT_SEC))
    layout["yaxis"]["title"] = dict(text="LTV ($)", font=dict(size=10, color=TEXT_SEC))
    layout["xaxis"]["tickprefix"] = "$"
    layout["yaxis"]["tickprefix"] = "$"
    fig.update_layout(**layout)
    return fig


# ── 6. Burn Rate Trend with Forecast ─────────────────────────────────────────
def burn_trend_forecast(df: pd.DataFrame) -> go.Figure:
    dates = pd.to_datetime(df["date"])
    burn  = df["total_burn"].tolist()

    # Simple linear forecast for next 6 months
    x_num = np.arange(len(burn))
    coeffs = np.polyfit(x_num[-6:], burn[-6:], 1)
    future_x = np.arange(len(burn), len(burn) + 6)
    forecast  = np.polyval(coeffs, future_x).tolist()

    future_dates = pd.date_range(
        start=dates.iloc[-1] + pd.DateOffset(months=1), periods=6, freq="MS"
    )

    fig = go.Figure()

    # Actual burn
    fig.add_trace(go.Scatter(
        x=dates, y=burn,
        line=dict(color=ACCENT3, width=2.5),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.07)",
        name="Actual Burn",
        hovertemplate="<b>%{x|%b %Y}</b><br>Burn: $%{y:,.0f}<extra></extra>",
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=list(future_dates), y=forecast,
        line=dict(color=ACCENT3, width=1.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.03)",
        name="Forecast",
        hovertemplate="<b>Forecast %{x|%b %Y}</b><br>$%{y:,.0f}<extra></extra>",
    ))

    # Separator
    fig.add_vline(
        x=str(dates.iloc[-1]), line_color=BORDER, line_width=1, line_dash="dash"
    )

    layout = _layout(height=240)
    layout["showlegend"] = True
    layout["legend"] = dict(
        orientation="h", y=-0.22, x=0,
        font=dict(family="'DM Mono', monospace", size=9, color=TEXT_SEC),
        bgcolor="rgba(0,0,0,0)",
    )
    layout["yaxis"]["tickprefix"] = "$"
    layout["yaxis"]["tickformat"] = ",.0s"
    fig.update_layout(**layout)
    return fig


# ── 7. Scenario Comparison Bar ────────────────────────────────────────────────
def scenario_comparison(base_runway, scenario_runway) -> go.Figure:
    labels = ["Base Case", "Scenario"]
    values = [base_runway, scenario_runway]
    colors = [ACCENT if v >= 12 else ACCENT3 if v >= 6 else DANGER for v in values]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        marker_opacity=0.85,
        text=[f"{v:.1f} mo" for v in values],
        textposition="outside",
        textfont=dict(family="'DM Mono', monospace", size=11, color=TEXT_PRI),
        hovertemplate="<b>%{x}</b>: %{y:.1f} months<extra></extra>",
    ))

    fig.add_hline(y=12, line_color=ACCENT3, line_width=1, line_dash="dot",
                  annotation_text="12-month target",
                  annotation_font_color=ACCENT3,
                  annotation_font_size=9)

    layout = _layout(height=200)
    layout["yaxis"]["title"] = dict(text="Months runway", font=dict(size=10))
    layout["yaxis"]["range"] = [0, max(values) * 1.3]
    fig.update_layout(**layout)
    return fig
