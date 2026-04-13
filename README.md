# 🔥 Burn Rate & Runway Monitor

> **A production-grade financial intelligence dashboard built for FinTech & SaaS founders.**
> Know your runway. Model your scenarios. Survive to Series A.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3b82f6?style=flat-square&logo=python&logoColor=white)
![Dash](https://img.shields.io/badge/Plotly_Dash-2.18-00d4aa?style=flat-square&logo=plotly&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.2-f59e0b?style=flat-square&logo=pandas&logoColor=white)
![Railway](https://img.shields.io/badge/Deployed_on-Railway-8b5cf6?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-10b981?style=flat-square)
![Built by](https://img.shields.io/badge/Built_by-MA_TechHub-ef4444?style=flat-square)

**[Live Demo →](https://burn-rate-monitor.up.railway.app)**  &nbsp;|&nbsp;  **[Portfolio →](https://anesu-manjengwa.vercel.app)**  &nbsp;|&nbsp;  **[MA TechHub →](https://matechhub.io)**

</div>

---

## What this is

Most startup founders check their bank balance and hope for the best.

This dashboard gives them what they actually need: a real-time view of burn rate, runway, MRR growth, and the ability to model what happens if they cut costs, raise money, or hire someone next month — before they do it.

Built as a portfolio project under the **MA TechHub** brand, targeting pre-seed and bootstrapped SaaS founders who need financial clarity without paying $500/month for Runway.com.

---

## Features

### Core Metrics
| Module | Description |
|--------|-------------|
| 💰 **Cash Balance Timeline** | Area chart with danger zone overlay (<$100K) and scenario overlay |
| ⏳ **Runway Gauge** | Visual gauge with colour-coded zones (green / amber / red) |
| 🔥 **Burn Breakdown** | Stacked bar chart: salaries, infra, marketing, software, office, misc |
| 📈 **MRR & Net Burn** | Revenue growth vs monthly cash outflow on one chart |
| 📊 **Burn Forecast** | 6-month linear trend projection from last 6 months of data |
| 🎯 **CAC vs LTV Scatter** | Customer acquisition cost vs lifetime value with 3:1 threshold line |

### Scenario Engine (Interactive)
- **Burn reduction slider** — Model what happens if you cut burn by 10–60%
- **Revenue injection** — Simulate closing a new contract or MRR uplift
- **Headcount modeling** — Add new hires at estimated $5K/month cost
- **Bridge fundraise** — Inject capital and see new runway instantly

### Alerts & Export
- **Danger zone banner** — Auto-triggered below 3 months runway (critical) and 6 months (warning)
- **Industry benchmarks** — Compare your burn vs B2B SaaS, Fintech, Dev Tools sector averages
- **Funding history** — Investor table with amounts, dates, and round types
- **PDF export** — Investor-ready report with full financials table (ReportLab)

---

## Tech Stack

```
Python 3.11          Core language
Plotly Dash 2.18     Reactive web framework + charting
Pandas 2.2           Data wrangling
NumPy 2.1            Scenario calculations & forecasting
ReportLab 4.2        PDF generation
Gunicorn 23          Production WSGI server
Railway / Render     Cloud deployment
```

---

## Project Structure

```
burn-rate-monitor/
│
├── app.py                    ← Main Dash application (entry point)
│
├── utils/
│   ├── charts.py             ← All 7 Plotly chart factories
│   └── export.py             ← ReportLab PDF generator
│
├── data/
│   ├── generate_data.py      ← Synthetic dataset generator
│   ├── financials.csv        ← 24 months of monthly financials
│   ├── benchmarks.json       ← Industry burn benchmarks by sector
│   └── investors.json        ← Funding history records
│
├── assets/
│   └── css/
│       └── style.css         ← Full custom dark theme stylesheet
│
├── requirements.txt
├── Procfile                  ← Gunicorn start command
├── railway.json              ← Railway deployment config
├── render.yaml               ← Render deployment config
└── README.md
```

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/Iceyma02/burn-rate-monitor.git
cd burn-rate-monitor
pip install -r requirements.txt
```

### 2. Generate data

```bash
python data/generate_data.py
```

### 3. Run locally

```bash
python app.py
# Open http://localhost:8050
```

---

## Deploy to Railway (recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login & init
railway login
railway init

# Deploy
railway up
```

Railway will auto-detect Python, install `requirements.txt`, and use the `Procfile` start command. The `$PORT` env var is injected automatically.

---

## Deploy to Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service → Connect repo
3. Render detects `render.yaml` and configures everything automatically
4. Done — live in ~3 minutes

---

## Using Your Own Data

Replace `data/financials.csv` with your real numbers. The CSV must have these columns:

```
date, salaries, infrastructure, marketing, software, office, misc,
total_burn, mrr, cash_balance, net_burn, runway_months
```

Dates in `YYYY-MM-DD` format. All monetary values in USD (no symbols).

To update benchmarks, edit `data/benchmarks.json`. To update investors, edit `data/investors.json`.

---

## Roadmap

- [ ] Multi-company support (switch between startups)
- [ ] CSV upload for real data ingestion
- [ ] Slack / email alerts when runway drops below threshold
- [ ] PostgreSQL backend for persistent storage
- [ ] Series A readiness score (composite metric)
- [ ] Cohort-level churn analysis

---

## About MA TechHub

**MA TechHub** is a data analytics and dashboard consultancy specialising in FinTech and SaaS intelligence tools.

We build production-grade dashboards that turn raw financial data into founder decisions.

- 🌐 [matechhub.io](https://matechhub.io)
- 💼 [anesu-manjengwa.vercel.app](https://anesu-manjengwa.vercel.app)
- 🐙 [github.com/Iceyma02](https://github.com/Iceyma02)
- 📧 contact@matechhub.io

---

## License

MIT — free to use, fork, and build on. Attribution appreciated.

---

<div align="center">

**Built with 🔥 by [Anesu Manjengwa](https://anesu-manjengwa.vercel.app) · MA TechHub**

*If this helped you, drop a ⭐ — it genuinely helps.*

</div>
