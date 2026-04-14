"""
app.py — Burn Rate & Runway Monitor
MA TechHub  |  github.com/Iceyma02
Production-grade Plotly Dash dashboard for FinTech / SaaS founders.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import json
import base64
from datetime import datetime

from utils.charts import (
    cash_balance_chart,
    burn_breakdown_chart,
    mrr_chart,
    runway_gauge,
    cac_ltv_chart,
    burn_trend_forecast,
    scenario_comparison,
)
from utils.export import generate_pdf

# ── Install dbc if needed ─────────────────────────────────────────────────────
# pip install dash-bootstrap-components

# ── Load data ─────────────────────────────────────────────────────────────────
df         = pd.read_csv("data/financials.csv", parse_dates=["date"])
benchmarks = json.load(open("data/benchmarks.json"))
investors  = json.load(open("data/investors.json"))

df = df.assign(runway_months=pd.to_numeric(df["runway_months"], errors="coerce").fillna(0))

latest = df.iloc[-1]
prior  = df.iloc[-2]

def fmt_usd(val):
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:.2f}M"
    if abs(val) >= 1_000:
        return f"${val/1_000:.1f}K"
    return f"${val:.0f}"

def delta_pct(new, old):
    if old == 0:
        return 0
    return round((new - old) / abs(old) * 100, 1)

# ── App init ──────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap",
    ],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Burn Rate Monitor | MA TechHub"
server = app.server


# ── Helper: KPI card ──────────────────────────────────────────────────────────
def kpi_card(label, value, delta, delta_label, color_class, icon):
    delta_class = "up" if delta > 0 else "down" if delta < 0 else "warn"
    arrow       = "▲" if delta > 0 else "▼" if delta < 0 else "—"

    # Flip logic: for burn, higher = worse (down = good)
    if label in ("MONTHLY BURN", "NET BURN"):
        delta_class = "down" if delta > 0 else "up"

    return html.Div([
        html.Div([
            html.Span(icon, style={"marginRight": "6px"}),
            label,
        ], className="kpi-label"),
        html.Div(value, className="kpi-value"),
        html.Div([
            html.Span(arrow),
            f" {abs(delta)}%  {delta_label}",
        ], className=f"kpi-delta {delta_class}"),
    ], className=f"kpi-card {color_class}")


# ── Helper: chart card ─────────────────────────────────────────────────────────
def chart_card(title, subtitle, badge_text, badge_class, graph_id, badge2=None):
    badge_els = [html.Span(badge_text, className=f"chart-badge {badge_class}")]
    if badge2:
        badge_els.append(html.Span(badge2[0], className=f"chart-badge {badge2[1]}",
                                   style={"marginLeft": "6px"}))
    return html.Div([
        html.Div([
            html.Div([
                html.Div(title, className="chart-title"),
                html.Div(subtitle, className="chart-sub"),
            ]),
            html.Div(badge_els),
        ], className="chart-header"),
        dcc.Graph(id=graph_id, config={"displayModeBar": False}),
    ], className="chart-card")


# ── Danger banner ─────────────────────────────────────────────────────────────
runway_val = float(latest["runway_months"])

def danger_banner():
    if runway_val < 3:
        return html.Div([
            html.Div("⚠", className="danger-icon"),
            html.Div([
                html.Div("CRITICAL — RUNWAY BELOW 3 MONTHS", className="danger-title"),
                html.Div(
                    f"Current runway: {runway_val:.1f} months  ·  Take action immediately.",
                    className="danger-msg",
                ),
            ], className="danger-text"),
        ], className="danger-banner")
    elif runway_val < 6:
        return html.Div([
            html.Div("⚡", className="danger-icon"),
            html.Div([
                html.Div("WARNING — RUNWAY BELOW 6 MONTHS", className="danger-title",
                         style={"color": "var(--warning)"}),
                html.Div(
                    f"Current runway: {runway_val:.1f} months  ·  Begin fundraising now.",
                    className="danger-msg", style={"color": "rgba(245,158,11,0.7)"},
                ),
            ], className="danger-text"),
        ], className="danger-banner",
           style={"borderColor": "rgba(245,158,11,0.3)",
                  "background": "rgba(245,158,11,0.06)"})
    return html.Div()


# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([

    # ── Top navigation ────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div("BR", className="brand-logo"),
            html.Div([
                html.Div([
                    "Burn Rate ",
                    html.Span("Monitor", style={"color": "var(--accent)"}),
                ], className="brand-title"),
                html.Div("MA TECHHUB  ·  SAAS FINANCIAL INTELLIGENCE", className="brand-subtitle"),
            ]),
        ], className="header-brand"),

        html.Div([
            html.Div([
                html.Div(className="live-dot"),
                f"Live  ·  {datetime.now().strftime('%b %d, %Y')}",
            ], className="live-badge"),
            html.A(
                ["↓  Export PDF"],
                id="export-btn",
                href="#",
                className="export-btn",
                style={"cursor": "pointer"},
            ),
            dcc.Download(id="download-pdf"),
        ], className="header-right"),

    ], id="header"),

    # Alert banner
    danger_banner(),

    # ── KPI Row ───────────────────────────────────────────────────────────────
    html.Div([
        kpi_card(
            "MONTHLY BURN",
            fmt_usd(latest["total_burn"]),
            delta_pct(latest["total_burn"], prior["total_burn"]),
            "vs last month",
            "amber",
            "🔥",
        ),
        kpi_card(
            "CASH BALANCE",
            fmt_usd(latest["cash_balance"]),
            delta_pct(latest["cash_balance"], prior["cash_balance"]),
            "vs last month",
            "green",
            "💰",
        ),
        kpi_card(
            "MRR",
            fmt_usd(latest["mrr"]),
            delta_pct(latest["mrr"], prior["mrr"]),
            "vs last month",
            "blue",
            "📈",
        ),
        kpi_card(
            "RUNWAY",
            f"{runway_val:.1f} mo",
            0,
            "at current burn",
            "red" if runway_val < 6 else "green",
            "⏳",
        ),
    ], id="kpi-row"),

    # ── Row 1: Cash balance + Runway gauge ────────────────────────────────────
    html.Div([
        chart_card(
            "Cash balance timeline",
            "Monthly cash position with danger zone overlay",
            "LIVE",   "badge-green",
            "cash-chart",
            badge2=("SCENARIO", "badge-blue"),
        ),
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Runway gauge", className="chart-title"),
                    html.Div("Months of runway at current net burn", className="chart-sub"),
                ]),
                html.Span(
                    "CRITICAL" if runway_val < 6 else "HEALTHY",
                    className=f"chart-badge {'badge-red' if runway_val < 6 else 'badge-green'}",
                ),
            ], className="chart-header"),
            dcc.Graph(
                id="runway-gauge",
                figure=runway_gauge(runway_val),
                config={"displayModeBar": False},
            ),
            html.Div([
                html.Div([
                    html.Div("Net Burn / mo", className="kpi-label"),
                    html.Div(fmt_usd(latest["net_burn"]), className="kpi-value",
                             style={"fontSize": "20px"}),
                ]),
                html.Div([
                    html.Div("Zero Date", className="kpi-label"),
                    html.Div(
                        (pd.to_datetime(latest["date"]) +
                         pd.DateOffset(months=max(0, int(runway_val)))).strftime("%b %Y"),
                        className="kpi-value", style={"fontSize": "20px", "color": "var(--danger)"},
                    ),
                ]),
            ], style={"display": "flex", "justifyContent": "space-around",
                      "marginTop": "10px"}),
        ], className="chart-card"),
    ], className="chart-grid-3"),

    # ── Row 2: Burn breakdown + MRR ───────────────────────────────────────────
    html.Div([
        chart_card(
            "Burn breakdown by category",
            "Fixed vs variable costs stacked monthly",
            "24 MONTHS", "badge-amber",
            "burn-breakdown",
        ),
        chart_card(
            "MRR & net burn",
            "Revenue growth vs monthly burn rate",
            "GROWTH", "badge-blue",
            "mrr-chart",
        ),
    ], className="chart-grid-2"),

    # ── Row 3: Burn forecast + CAC/LTV ────────────────────────────────────────
    html.Div([
        chart_card(
            "Burn trend & 6-month forecast",
            "Linear trend projection based on last 6 months",
            "FORECAST", "badge-amber",
            "burn-forecast",
        ),
        chart_card(
            "CAC vs LTV scatter",
            "Customer acquisition cost vs lifetime value — 3:1 threshold line",
            "LTV:CAC", "badge-green",
            "cac-ltv",
        ),
    ], className="chart-grid-2"),

    # ── Row 4: Scenario engine ────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div([
                html.Div("Scenario engine", className="chart-title"),
                html.Div("Model burn changes, fundraising, and headcount", className="chart-sub"),
            ]),
            html.Span("INTERACTIVE", className="chart-badge badge-blue"),
        ], className="chart-header"),

        # Tabs
        html.Div([
            html.Button("Burn Reduction", id="tab-burn", className="tab-btn active"),
            html.Button("Revenue Injection", id="tab-revenue", className="tab-btn"),
            html.Button("New Hire", id="tab-hire", className="tab-btn"),
            html.Button("Fundraise", id="tab-raise", className="tab-btn"),
        ], className="tab-bar"),

        # Controls
        html.Div(id="scenario-controls", children=[
            html.Div([
                html.Div([
                    html.Div([
                        "Burn reduction %",
                        html.Span(id="burn-pct-label", children="0%"),
                    ], className="slider-label"),
                    dcc.Slider(
                        id="burn-pct", min=0, max=60, step=5, value=0,
                        marks={0:"0%",20:"20%",40:"40%",60:"60%"},
                        tooltip={"always_visible": False},
                    ),
                ], className="slider-group"),
                html.Div([
                    html.Div([
                        "New MRR / month ($)",
                        html.Span(id="new-mrr-label", children="$0"),
                    ], className="slider-label"),
                    dcc.Slider(
                        id="new-mrr", min=0, max=20000, step=500, value=0,
                        marks={0:"$0", 10000:"$10K", 20000:"$20K"},
                        tooltip={"always_visible": False},
                    ),
                ], className="slider-group"),
            ], className="scenario-grid"),
            html.Div([
                html.Div([
                    html.Div([
                        "New hires",
                        html.Span(id="hire-label", children="0"),
                    ], className="slider-label"),
                    dcc.Slider(
                        id="new-hires", min=0, max=10, step=1, value=0,
                        marks={0:"0",5:"5",10:"10"},
                        tooltip={"always_visible": False},
                    ),
                ], className="slider-group"),
                html.Div([
                    html.Div([
                        "Bridge funding ($)",
                        html.Span(id="raise-label", children="$0"),
                    ], className="slider-label"),
                    dcc.Slider(
                        id="bridge-raise", min=0, max=1000000, step=50000, value=0,
                        marks={0:"$0", 500000:"$500K", 1000000:"$1M"},
                        tooltip={"always_visible": False},
                    ),
                ], className="slider-group"),
            ], className="scenario-grid"),
        ]),

        # Output charts
        html.Div([
            html.Div([
                dcc.Graph(id="scenario-cash", config={"displayModeBar": False}),
            ], style={"flex": "1"}),
            html.Div([
                dcc.Graph(id="scenario-bar", config={"displayModeBar": False}),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "16px"}),

    ], className="chart-card", style={"marginBottom": "16px"}),

    # ── Row 5: Benchmarks + Investor table ───────────────────────────────────
    html.Div([

        # Benchmarks
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Industry benchmarks", className="chart-title"),
                    html.Div("Monthly burn vs sector averages", className="chart-sub"),
                ]),
                html.Span("COMPARISON", className="chart-badge badge-blue"),
            ], className="chart-header"),
            html.Div(id="benchmark-table"),
        ], className="chart-card"),

        # Investors
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Funding history", className="chart-title"),
                    html.Div("Capital raises and investor summary", className="chart-sub"),
                ]),
                html.Span("CONFIDENTIAL", className="chart-badge badge-red"),
            ], className="chart-header"),
            html.Div(id="investor-table"),
        ], className="chart-card"),

    ], className="chart-grid-2"),

    # ── Footer ────────────────────────────────────────────────────────────────
    html.Div([
        html.Div(
            ["Built by ", html.A("MA TechHub", href="https://anesu-manjengwa.vercel.app",
                                 target="_blank"),
             " · Burn Rate Monitor v1.0 · Plotly Dash"],
            className="footer-text",
        ),
        html.Div(
            f"Data as of {latest['date'].strftime('%B %Y')}  ·  {len(df)} months of history",
            className="footer-text",
        ),
    ], id="footer"),

], id="app-wrapper")


# ═════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ═════════════════════════════════════════════════════════════════════════════

# ── 1. Cash balance chart ──────────────────────────────────────────────────────
@app.callback(
    Output("cash-chart", "figure"),
    Input("burn-pct", "value"),
    Input("new-mrr", "value"),
    Input("new-hires", "value"),
    Input("bridge-raise", "value"),
)
def update_cash_chart(burn_pct, new_mrr, new_hires, bridge):
    burn_pct  = burn_pct  or 0
    new_mrr   = new_mrr   or 0
    new_hires = new_hires or 0
    bridge    = bridge    or 0

    hire_cost = new_hires * 5000   # avg $5k/month per hire
    reduction = burn_pct / 100

    scenario_cash = [df.iloc[0]["cash_balance"] + bridge]
    for i in range(1, len(df)):
        base_burn = df.iloc[i]["total_burn"]
        adj_burn  = base_burn * (1 - reduction) + hire_cost
        mrr_boost = df.iloc[i]["mrr"] + new_mrr
        net       = adj_burn - mrr_boost
        scenario_cash.append(scenario_cash[-1] - net)

    return cash_balance_chart(df, scenario_cash)


# ── 2. Scenario bar ────────────────────────────────────────────────────────────
@app.callback(
    Output("scenario-bar", "figure"),
    Output("scenario-cash", "figure"),
    Input("burn-pct", "value"),
    Input("new-mrr", "value"),
    Input("new-hires", "value"),
    Input("bridge-raise", "value"),
)
def update_scenario(burn_pct, new_mrr, new_hires, bridge):
    burn_pct  = burn_pct  or 0
    new_mrr   = new_mrr   or 0
    new_hires = new_hires or 0
    bridge    = bridge    or 0

    hire_cost   = new_hires * 5000
    reduction   = burn_pct / 100

    base_net    = float(latest["net_burn"])
    scenario_net= base_net * (1 - reduction) + hire_cost - new_mrr
    base_cash   = float(latest["cash_balance"])
    scen_cash   = base_cash + bridge

    base_runway = round(base_cash / max(base_net, 1), 1)
    scen_runway = round(scen_cash / max(scenario_net, 1), 1)

    # Rebuild scenario cash series
    scenario_cash = [df.iloc[0]["cash_balance"] + bridge]
    for i in range(1, len(df)):
        base_burn = df.iloc[i]["total_burn"]
        adj_burn  = base_burn * (1 - reduction) + hire_cost
        mrr_boost = df.iloc[i]["mrr"] + new_mrr
        net       = adj_burn - mrr_boost
        scenario_cash.append(scenario_cash[-1] - net)

    return (
        scenario_comparison(base_runway, scen_runway),
        cash_balance_chart(df, scenario_cash),
    )


# ── 3. Slider labels ───────────────────────────────────────────────────────────
@app.callback(
    Output("burn-pct-label", "children"),
    Output("new-mrr-label",  "children"),
    Output("hire-label",     "children"),
    Output("raise-label",    "children"),
    Input("burn-pct",    "value"),
    Input("new-mrr",     "value"),
    Input("new-hires",   "value"),
    Input("bridge-raise","value"),
)
def update_labels(bp, nm, nh, br):
    return (
        f"{bp or 0}%",
        f"${(nm or 0):,.0f}",
        str(nh or 0),
        f"${(br or 0):,.0f}",
    )


# ── 4. Static charts ───────────────────────────────────────────────────────────
@app.callback(
    Output("burn-breakdown", "figure"),
    Output("mrr-chart",      "figure"),
    Output("burn-forecast",  "figure"),
    Output("cac-ltv",        "figure"),
    Input("burn-pct", "value"),   # dummy trigger so they load
)
def load_static_charts(_):
    return (
        burn_breakdown_chart(df),
        mrr_chart(df),
        burn_trend_forecast(df),
        cac_ltv_chart(df),
    )


# ── 5. Benchmarks ──────────────────────────────────────────────────────────────
@app.callback(Output("benchmark-table", "children"), Input("burn-pct", "value"))
def render_benchmarks(_):
    current_burn = float(latest["total_burn"])
    max_burn = max(d["avg_burn"] for d in benchmarks.values())
    rows = []
    for sector, data in benchmarks.items():
        avg = data["avg_burn"]
        width = int(avg / max_burn * 100)
        is_you = current_burn <= avg * 1.2 and current_burn >= avg * 0.8
        bar_color = "var(--accent)" if is_you else "var(--accent2)"
        rows.append(html.Div([
            html.Div(sector + (" ← you" if is_you else ""), className="bm-name",
                     style={"color": "var(--accent)" if is_you else None}),
            html.Div(html.Div(style={
                "width": f"{width}%", "background": bar_color,
            }), className="bm-bar-wrap"),
            html.Div(f"${avg:,.0f}/mo", className="bm-value"),
        ], className="benchmark-row"))
    return rows


# ── 6. Investor table ──────────────────────────────────────────────────────────
@app.callback(Output("investor-table", "children"), Input("burn-pct", "value"))
def render_investors(_):
    total = sum(i["amount"] for i in investors)
    rows = []
    for inv in investors:
        type_colors = {"Lead": "badge-amber", "Program": "badge-blue",
                       "Angel": "badge-green", "Bridge": "badge-red"}
        rows.append(html.Div([
            html.Div([
                html.Div(inv["name"], style={
                    "fontFamily": "var(--font-data)", "fontSize": "12px",
                    "color": "var(--text-primary)",
                }),
                html.Div(inv["date"], style={
                    "fontFamily": "var(--font-data)", "fontSize": "10px",
                    "color": "var(--text-muted)",
                }),
            ], style={"flex": "1"}),
            html.Span(inv["type"], className=f"chart-badge {type_colors.get(inv['type'],'badge-blue')}"),
            html.Div(f"${inv['amount']:,.0f}", style={
                "fontFamily": "var(--font-data)", "fontSize": "12px",
                "color": "var(--text-primary)", "minWidth": "80px", "textAlign": "right",
            }),
        ], style={
            "display": "flex", "alignItems": "center", "gap": "12px",
            "padding": "10px 0", "borderBottom": "1px solid var(--border)",
        }))

    rows.append(html.Div([
        html.Div("TOTAL RAISED", style={
            "flex": "1", "fontFamily": "var(--font-data)",
            "fontSize": "10px", "letterSpacing": "0.1em",
            "color": "var(--text-muted)",
        }),
        html.Div(f"${total:,.0f}", style={
            "fontFamily": "var(--font-data)", "fontSize": "14px",
            "fontWeight": "700", "color": "var(--accent)",
        }),
    ], style={"display": "flex", "justifyContent": "space-between",
              "paddingTop": "12px"}))
    return rows


# ── 7. PDF export ──────────────────────────────────────────────────────────────
@app.callback(
    Output("download-pdf", "data"),
    Input("export-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_pdf(n):
    if not n:
        return dash.no_update
    pdf_bytes = generate_pdf(df, {})
    return dcc.send_bytes(pdf_bytes, filename="burn-rate-report.pdf")


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)
