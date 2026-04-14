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
from datetime import datetime

from utils.charts import (
    cash_balance_chart, burn_breakdown_chart, mrr_chart,
    runway_gauge, cac_ltv_chart, burn_trend_forecast, scenario_comparison,
)
from utils.export import generate_pdf

# ── Load data ─────────────────────────────────────────────────────────────────
_raw       = pd.read_csv("data/financials.csv", dtype={"date": "object"})
benchmarks = json.load(open("data/benchmarks.json"))
investors  = json.load(open("data/investors.json"))

df = pd.DataFrame({
    **{c: _raw[c] for c in _raw.columns if c not in ("date", "runway_months")},
    "date":          pd.to_datetime(_raw["date"]),
    "runway_months": pd.to_numeric(_raw["runway_months"], errors="coerce").fillna(0),
})

latest = df.iloc[-1]
prior  = df.iloc[-2]

def fmt_usd(val):
    if abs(val) >= 1_000_000: return f"${val/1_000_000:.2f}M"
    if abs(val) >= 1_000:     return f"${val/1_000:.1f}K"
    return f"${val:.0f}"

def delta_pct(new, old):
    if old == 0: return 0
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


# ── UI helpers ────────────────────────────────────────────────────────────────
def kpi_card(label, value, delta, delta_label, color_class, icon):
    delta_class = "up" if delta > 0 else "down" if delta < 0 else "warn"
    arrow = "▲" if delta > 0 else "▼" if delta < 0 else "—"
    if label in ("MONTHLY BURN", "NET BURN"):
        delta_class = "down" if delta > 0 else "up"
    return html.Div([
        html.Div([html.Span(icon, style={"marginRight": "6px"}), label], className="kpi-label"),
        html.Div(value, className="kpi-value"),
        html.Div([html.Span(arrow), f" {abs(delta)}%  {delta_label}"],
                 className=f"kpi-delta {delta_class}"),
    ], className=f"kpi-card {color_class}")


def chart_card(title, subtitle, badge_text, badge_class, graph_id, badge2=None):
    badge_els = [html.Span(badge_text, className=f"chart-badge {badge_class}")]
    if badge2:
        badge_els.append(html.Span(badge2[0], className=f"chart-badge {badge2[1]}",
                                   style={"marginLeft": "6px"}))
    return html.Div([
        html.Div([
            html.Div([html.Div(title, className="chart-title"),
                      html.Div(subtitle, className="chart-sub")]),
            html.Div(badge_els),
        ], className="chart-header"),
        dcc.Graph(id=graph_id, config={"displayModeBar": False}),
    ], className="chart-card")


def danger_banner():
    rw = float(latest["runway_months"])
    if rw < 3:
        return html.Div([
            html.Div("⚠", className="danger-icon"),
            html.Div([
                html.Div("CRITICAL — RUNWAY BELOW 3 MONTHS", className="danger-title"),
                html.Div(f"Current runway: {rw:.1f} months  ·  Take action immediately.",
                         className="danger-msg"),
            ], className="danger-text"),
        ], className="danger-banner")
    elif rw < 6:
        return html.Div([
            html.Div("⚡", className="danger-icon"),
            html.Div([
                html.Div("WARNING — RUNWAY BELOW 6 MONTHS", className="danger-title",
                         style={"color": "var(--warning)"}),
                html.Div(f"Current runway: {rw:.1f} months  ·  Begin fundraising now.",
                         className="danger-msg", style={"color": "rgba(245,158,11,0.7)"}),
            ], className="danger-text"),
        ], className="danger-banner",
           style={"borderColor": "rgba(245,158,11,0.3)", "background": "rgba(245,158,11,0.06)"})
    return html.Div()


runway_val     = float(latest["runway_months"])
runway_display = f"{runway_val:.1f} mo" if runway_val < 99 else "Profitable"
runway_color   = "red" if runway_val < 6 else "amber" if runway_val < 12 else "green"


# ── Tab panels ────────────────────────────────────────────────────────────────
def _hint_style():
    return {"fontFamily": "var(--font-data)", "fontSize": "11px",
            "color": "var(--text-muted)", "marginTop": "8px"}

def tab_panel_burn():
    return html.Div([
        html.Div([
            html.Div([
                html.Div(["Cut monthly burn by",
                          html.Span(id="burn-pct-label", children=" 0%")],
                         className="slider-label"),
                dcc.Slider(id="burn-pct", min=0, max=60, step=5, value=0,
                           marks={0:"0%",20:"20%",40:"40%",60:"60%"},
                           tooltip={"always_visible": False}),
            ], className="slider-group"),
            html.Div([
                html.Div(["Runway extension",
                          html.Span(id="burn-impact-label", children=" —",
                                    style={"color": "var(--accent)"})],
                         className="slider-label"),
                html.Div(id="burn-hint", style=_hint_style()),
            ], className="slider-group"),
        ], className="scenario-grid"),
    ])


def tab_panel_revenue():
    return html.Div([
        html.Div([
            html.Div([
                html.Div(["New MRR / month",
                          html.Span(id="new-mrr-label", children=" $0")],
                         className="slider-label"),
                dcc.Slider(id="new-mrr", min=0, max=30000, step=1000, value=0,
                           marks={0:"$0",15000:"$15K",30000:"$30K"},
                           tooltip={"always_visible": False}),
            ], className="slider-group"),
            html.Div([
                html.Div(["Runway extension",
                          html.Span(id="mrr-impact-label", children=" —",
                                    style={"color": "var(--accent2)"})],
                         className="slider-label"),
                html.Div(id="revenue-hint", style=_hint_style()),
            ], className="slider-group"),
        ], className="scenario-grid"),
    ])


def tab_panel_hire():
    return html.Div([
        html.Div([
            html.Div([
                html.Div(["New hires",
                          html.Span(id="hire-label", children=" 0")],
                         className="slider-label"),
                dcc.Slider(id="new-hires", min=0, max=10, step=1, value=0,
                           marks={0:"0",5:"5",10:"10"},
                           tooltip={"always_visible": False}),
            ], className="slider-group"),
            html.Div([
                html.Div(["Monthly cost added",
                          html.Span(id="hire-cost-label", children=" $0",
                                    style={"color": "var(--danger)"})],
                         className="slider-label"),
                html.Div(id="hire-hint", style=_hint_style()),
            ], className="slider-group"),
        ], className="scenario-grid"),
    ])


def tab_panel_raise():
    return html.Div([
        html.Div([
            html.Div([
                html.Div(["Bridge / Series funding",
                          html.Span(id="raise-label", children=" $0")],
                         className="slider-label"),
                dcc.Slider(id="bridge-raise", min=0, max=2000000, step=100000, value=0,
                           marks={0:"$0",1000000:"$1M",2000000:"$2M"},
                           tooltip={"always_visible": False}),
            ], className="slider-group"),
            html.Div([
                html.Div(["Runway extension",
                          html.Span(id="raise-impact-label", children=" —",
                                    style={"color": "var(--accent)"})],
                         className="slider-label"),
                html.Div(id="raise-hint", style=_hint_style()),
            ], className="slider-group"),
        ], className="scenario-grid"),
    ])


# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([

    html.Div([
        html.Div([
            html.Div("BR", className="brand-logo"),
            html.Div([
                html.Div(["Burn Rate ",
                          html.Span("Monitor", style={"color": "var(--accent)"})],
                         className="brand-title"),
                html.Div("MA TECHHUB  ·  SAAS FINANCIAL INTELLIGENCE",
                         className="brand-subtitle"),
            ]),
        ], className="header-brand"),
        html.Div([
            html.Div([html.Div(className="live-dot"),
                      f"Live  ·  {datetime.now().strftime('%b %d, %Y')}"],
                     className="live-badge"),
            html.A("↓  Export PDF", id="export-btn", href="#",
                   className="export-btn", style={"cursor": "pointer"}),
            dcc.Download(id="download-pdf"),
        ], className="header-right"),
    ], id="header"),

    danger_banner(),

    html.Div([
        kpi_card("MONTHLY BURN", fmt_usd(latest["total_burn"]),
                 delta_pct(latest["total_burn"], prior["total_burn"]),
                 "vs last month", "amber", "🔥"),
        kpi_card("CASH BALANCE", fmt_usd(latest["cash_balance"]),
                 delta_pct(latest["cash_balance"], prior["cash_balance"]),
                 "vs last month", "green", "💰"),
        kpi_card("MRR", fmt_usd(latest["mrr"]),
                 delta_pct(latest["mrr"], prior["mrr"]),
                 "vs last month", "blue", "📈"),
        kpi_card("RUNWAY", runway_display, 0, "at current burn", runway_color, "⏳"),
    ], id="kpi-row"),

    html.Div([
        chart_card("Cash balance timeline",
                   "Monthly cash position with danger zone overlay",
                   "LIVE", "badge-green", "cash-chart",
                   badge2=("SCENARIO", "badge-blue")),
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Runway gauge", className="chart-title"),
                    html.Div("Months of runway at current net burn", className="chart-sub"),
                ]),
                html.Span(
                    "CRITICAL" if runway_val < 6 else
                    "WARNING"  if runway_val < 12 else "HEALTHY",
                    className=f"chart-badge {'badge-red' if runway_val < 6 else 'badge-amber' if runway_val < 12 else 'badge-green'}",
                ),
            ], className="chart-header"),
            dcc.Graph(id="runway-gauge", figure=runway_gauge(runway_val),
                      config={"displayModeBar": False}),
            html.Div([
                html.Div([
                    html.Div("Net Burn / mo", className="kpi-label"),
                    html.Div(fmt_usd(latest["net_burn"]), className="kpi-value",
                             style={"fontSize": "20px",
                                    "color": "var(--danger)" if latest["net_burn"] > 0
                                             else "var(--success)"}),
                ]),
                html.Div([
                    html.Div("Zero Date", className="kpi-label"),
                    html.Div(
                        (latest["date"] +
                         pd.DateOffset(months=max(0, int(runway_val)))).strftime("%b %Y")
                        if runway_val < 99 else "Profitable ✓",
                        className="kpi-value",
                        style={"fontSize": "20px",
                               "color": "var(--success)" if runway_val >= 24
                                        else "var(--danger)"},
                    ),
                ]),
            ], style={"display": "flex", "justifyContent": "space-around",
                      "marginTop": "10px"}),
        ], className="chart-card"),
    ], className="chart-grid-3"),

    html.Div([
        chart_card("Burn breakdown by category",
                   "Fixed vs variable costs stacked monthly",
                   "24 MONTHS", "badge-amber", "burn-breakdown"),
        chart_card("MRR & net burn",
                   "Revenue growth vs monthly burn rate",
                   "GROWTH", "badge-blue", "mrr-chart"),
    ], className="chart-grid-2"),

    html.Div([
        chart_card("Burn trend & 6-month forecast",
                   "Linear trend projection based on last 6 months",
                   "FORECAST", "badge-amber", "burn-forecast"),
        chart_card("CAC vs LTV scatter",
                   "Customer acquisition cost vs lifetime value — 3:1 threshold line",
                   "LTV:CAC", "badge-green", "cac-ltv"),
    ], className="chart-grid-2"),

    # Scenario engine
    html.Div([
        html.Div([
            html.Div([
                html.Div("Scenario engine", className="chart-title"),
                html.Div("Model the impact of cost cuts, revenue growth, hiring, and fundraising",
                         className="chart-sub"),
            ]),
            html.Span("INTERACTIVE", className="chart-badge badge-blue"),
        ], className="chart-header"),

        html.Div([
            html.Button("🔥  Burn Reduction",    id="tab-burn",    className="tab-btn active", n_clicks=0),
            html.Button("📈  Revenue Injection",  id="tab-revenue", className="tab-btn", n_clicks=0),
            html.Button("👥  New Hire",           id="tab-hire",    className="tab-btn", n_clicks=0),
            html.Button("💸  Fundraise",          id="tab-raise",   className="tab-btn", n_clicks=0),
        ], className="tab-bar"),

        html.Div(id="scenario-panel", children=tab_panel_burn()),

        # Stores persist values across tab switches
        dcc.Store(id="store-burn-pct",     data=0),
        dcc.Store(id="store-new-mrr",      data=0),
        dcc.Store(id="store-new-hires",    data=0),
        dcc.Store(id="store-bridge-raise", data=0),
        dcc.Store(id="active-tab",         data="burn"),

        html.Div([
            html.Div([dcc.Graph(id="scenario-cash", config={"displayModeBar": False})],
                     style={"flex": "1"}),
            html.Div([dcc.Graph(id="scenario-bar",  config={"displayModeBar": False})],
                     style={"flex": "1"}),
        ], style={"display": "flex", "gap": "16px", "marginTop": "16px"}),

    ], className="chart-card", style={"marginBottom": "16px"}),

    html.Div([
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

    html.Div([
        html.Div(["Built by ",
                  html.A("MA TechHub", href="https://anesu-manjengwa.vercel.app",
                         target="_blank"),
                  " · Burn Rate Monitor v1.1 · Plotly Dash"],
                 className="footer-text"),
        html.Div(
            f"Data as of {latest['date'].strftime('%B %Y')}  ·  {len(df)} months of history",
            className="footer-text"),
    ], id="footer"),

], id="app-wrapper")


# ═════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ═════════════════════════════════════════════════════════════════════════════

# ── Tab switching ──────────────────────────────────────────────────────────────
@app.callback(
    Output("scenario-panel", "children"),
    Output("active-tab",         "data"),
    Output("tab-burn",           "className"),
    Output("tab-revenue",        "className"),
    Output("tab-hire",           "className"),
    Output("tab-raise",          "className"),
    Output("store-burn-pct",     "data", allow_duplicate=True),
    Output("store-new-mrr",      "data", allow_duplicate=True),
    Output("store-new-hires",    "data", allow_duplicate=True),
    Output("store-bridge-raise", "data", allow_duplicate=True),
    Input("tab-burn",    "n_clicks"),
    Input("tab-revenue", "n_clicks"),
    Input("tab-hire",    "n_clicks"),
    Input("tab-raise",   "n_clicks"),
    State("active-tab",  "data"),
    prevent_initial_call="initial_duplicate",
)
def switch_tab(nb, nr, nh, nf, current):
    ctx = callback_context
    if not ctx.triggered:
        return tab_panel_burn(), "burn", "tab-btn active","tab-btn","tab-btn","tab-btn", 0,0,0,0
    tid = ctx.triggered[0]["prop_id"].split(".")[0]
    mapping = {
        "tab-burn":    ("burn",    tab_panel_burn()),
        "tab-revenue": ("revenue", tab_panel_revenue()),
        "tab-hire":    ("hire",    tab_panel_hire()),
        "tab-raise":   ("raise",   tab_panel_raise()),
    }
    name, panel = mapping.get(tid, ("burn", tab_panel_burn()))
    c = {t: "tab-btn active" if t == f"tab-{name}" else "tab-btn"
         for t in ["tab-burn","tab-revenue","tab-hire","tab-raise"]}
    return panel, name, c["tab-burn"], c["tab-revenue"], c["tab-hire"], c["tab-raise"], 0,0,0,0


# ── Store values when sliders change ──────────────────────────────────────────
@app.callback(Output("store-burn-pct","data"),
              Input("burn-pct","value"), prevent_initial_call=True)
def store_burn(v): return v or 0

@app.callback(Output("store-new-mrr","data"),
              Input("new-mrr","value"), prevent_initial_call=True)
def store_mrr(v): return v or 0

@app.callback(Output("store-new-hires","data"),
              Input("new-hires","value"), prevent_initial_call=True)
def store_hires(v): return v or 0

@app.callback(Output("store-bridge-raise","data"),
              Input("bridge-raise","value"), prevent_initial_call=True)
def store_raise(v): return v or 0


# ── Inline impact labels ───────────────────────────────────────────────────────
@app.callback(
    Output("burn-pct-label","children"),
    Output("burn-impact-label","children"),
    Output("burn-hint","children"),
    Input("burn-pct","value"),
)
def lbl_burn(bp):
    bp = bp or 0
    net = float(latest["net_burn"])
    new_net = net * (1 - bp/100)
    cash = float(latest["cash_balance"])
    base_rw = round(cash / max(net, 1), 1)
    new_rw  = round(cash / max(new_net, 0.01), 1)
    delta   = round(new_rw - base_rw, 1)
    hint = f"Net burn: {fmt_usd(net)}/mo → {fmt_usd(new_net)}/mo  ·  saving {fmt_usd(net-new_net)}/mo"
    return f" {bp}%", f" +{delta} months", hint

@app.callback(
    Output("new-mrr-label","children"),
    Output("mrr-impact-label","children"),
    Output("revenue-hint","children"),
    Input("new-mrr","value"),
)
def lbl_revenue(nm):
    nm = nm or 0
    mrr_now = float(latest["mrr"])
    net = float(latest["net_burn"])
    new_net = max(net - nm, 0.01)
    cash = float(latest["cash_balance"])
    base_rw = round(cash / max(net, 1), 1)
    new_rw  = round(cash / new_net, 1)
    delta   = round(new_rw - base_rw, 1)
    hint = f"MRR: {fmt_usd(mrr_now)} → {fmt_usd(mrr_now+nm)}/mo  ·  +{round(nm/mrr_now*100,1)}% uplift"
    return f" {fmt_usd(nm)}", f" +{delta} months", hint

@app.callback(
    Output("hire-label","children"),
    Output("hire-cost-label","children"),
    Output("hire-hint","children"),
    Input("new-hires","value"),
)
def lbl_hire(nh):
    nh = nh or 0
    cost = nh * 5500
    net  = float(latest["net_burn"])
    new_net = net + cost
    cash = float(latest["cash_balance"])
    base_rw = round(cash / max(net, 1), 1)
    new_rw  = round(cash / max(new_net, 1), 1)
    delta   = round(new_rw - base_rw, 1)
    hint = f"Cost: +{fmt_usd(cost)}/mo  ·  Net burn: {fmt_usd(net)} → {fmt_usd(new_net)}/mo  ·  {delta} months impact"
    return f" {nh}", f" {fmt_usd(cost)}", hint

@app.callback(
    Output("raise-label","children"),
    Output("raise-impact-label","children"),
    Output("raise-hint","children"),
    Input("bridge-raise","value"),
)
def lbl_raise(br):
    br = br or 0
    net  = float(latest["net_burn"])
    cash = float(latest["cash_balance"])
    base_rw = round(cash / max(net, 1), 1)
    new_rw  = round((cash + br) / max(net, 1), 1)
    delta   = round(new_rw - base_rw, 1)
    hint = f"Cash: {fmt_usd(cash)} → {fmt_usd(cash+br)}  ·  Zero date pushed by {delta} months"
    return f" {fmt_usd(br)}", f" +{delta} months", hint


# ── Scenario charts ────────────────────────────────────────────────────────────
def _build_scenario(burn_pct, new_mrr, new_hires, bridge):
    reduction = (burn_pct or 0) / 100
    hire_cost = (new_hires or 0) * 5500
    nm        = new_mrr or 0
    br        = bridge  or 0

    sc = [float(df.iloc[0]["cash_balance"]) + br]
    for i in range(1, len(df)):
        adj  = df.iloc[i]["total_burn"] * (1 - reduction) + hire_cost
        mrr_ = df.iloc[i]["mrr"] + nm
        sc.append(sc[-1] - (adj - mrr_))

    net      = float(latest["net_burn"])
    scen_net = net * (1 - reduction) + hire_cost - nm
    cash     = float(latest["cash_balance"])
    base_rw  = round(cash / max(net, 1), 1)
    scen_rw  = round((cash + br) / max(scen_net, 0.01), 1) if scen_net > 0 else 99
    return sc, base_rw, min(scen_rw, 60)


@app.callback(
    Output("scenario-cash","figure"),
    Output("scenario-bar","figure"),
    Output("cash-chart","figure"),
    Input("store-burn-pct","data"),
    Input("store-new-mrr","data"),
    Input("store-new-hires","data"),
    Input("store-bridge-raise","data"),
)
def update_scenarios(bp, nm, nh, br):
    sc, base_rw, scen_rw = _build_scenario(bp, nm, nh, br)
    return (cash_balance_chart(df, sc),
            scenario_comparison(base_rw, scen_rw),
            cash_balance_chart(df, sc))


# ── Static charts ──────────────────────────────────────────────────────────────
@app.callback(
    Output("burn-breakdown","figure"),
    Output("mrr-chart","figure"),
    Output("burn-forecast","figure"),
    Output("cac-ltv","figure"),
    Input("store-burn-pct","data"),
)
def load_static(_):
    return (burn_breakdown_chart(df), mrr_chart(df),
            burn_trend_forecast(df), cac_ltv_chart(df))


# ── Benchmarks ─────────────────────────────────────────────────────────────────
@app.callback(Output("benchmark-table","children"), Input("store-burn-pct","data"))
def render_benchmarks(_):
    cb = float(latest["total_burn"])
    mx = max(d["avg_burn"] for d in benchmarks.values())
    rows = []
    for sector, data in benchmarks.items():
        avg    = data["avg_burn"]
        w      = int(avg / mx * 100)
        is_you = cb <= avg * 1.25 and cb >= avg * 0.75
        rows.append(html.Div([
            html.Div(sector + (" ← you" if is_you else ""), className="bm-name",
                     style={"color": "var(--accent)" if is_you else None}),
            html.Div(html.Div(style={"width": f"{w}%",
                                     "background": "var(--accent)" if is_you else "var(--accent2)"}),
                     className="bm-bar-wrap"),
            html.Div(f"${avg:,.0f}/mo", className="bm-value"),
        ], className="benchmark-row"))
    return rows


# ── Investors ──────────────────────────────────────────────────────────────────
@app.callback(Output("investor-table","children"), Input("store-burn-pct","data"))
def render_investors(_):
    total = sum(i["amount"] for i in investors)
    tc = {"Lead":"badge-amber","Program":"badge-blue","Angel":"badge-green","Bridge":"badge-red"}
    rows = []
    for inv in investors:
        rows.append(html.Div([
            html.Div([
                html.Div(inv["name"], style={"fontFamily":"var(--font-data)","fontSize":"12px","color":"var(--text-primary)"}),
                html.Div(inv["date"], style={"fontFamily":"var(--font-data)","fontSize":"10px","color":"var(--text-muted)"}),
            ], style={"flex":"1"}),
            html.Span(inv["type"], className=f"chart-badge {tc.get(inv['type'],'badge-blue')}"),
            html.Div(f"${inv['amount']:,.0f}", style={"fontFamily":"var(--font-data)","fontSize":"12px","color":"var(--text-primary)","minWidth":"80px","textAlign":"right"}),
        ], style={"display":"flex","alignItems":"center","gap":"12px","padding":"10px 0","borderBottom":"1px solid var(--border)"}))
    rows.append(html.Div([
        html.Div("TOTAL RAISED", style={"flex":"1","fontFamily":"var(--font-data)","fontSize":"10px","letterSpacing":"0.1em","color":"var(--text-muted)"}),
        html.Div(f"${total:,.0f}", style={"fontFamily":"var(--font-data)","fontSize":"14px","fontWeight":"700","color":"var(--accent)"}),
    ], style={"display":"flex","justifyContent":"space-between","paddingTop":"12px"}))
    return rows


# ── PDF export ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("download-pdf","data"),
    Input("export-btn","n_clicks"),
    prevent_initial_call=True,
)
def export_pdf(n):
    if not n: return dash.no_update
    return dcc.send_bytes(generate_pdf(df, {}), filename="burn-rate-report.pdf")


if __name__ == "__main__":
    app.run(debug=True, port=8050)
