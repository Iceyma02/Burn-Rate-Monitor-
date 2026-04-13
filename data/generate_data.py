import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json, os

np.random.seed(42)

# ── 24 months of monthly financials ──────────────────────────────────────────
months = pd.date_range(start="2023-01-01", periods=24, freq="MS")

salaries      = [38000 + i*800  + np.random.randint(-500, 500)   for i in range(24)]
infrastructure= [4200  + i*120  + np.random.randint(-200, 200)   for i in range(24)]
marketing     = [6000  + i*400  + np.random.randint(-800, 800)   for i in range(24)]
software      = [2800  + i*50   + np.random.randint(-100, 100)   for i in range(24)]
office        = [3200  + np.random.randint(-100, 100)            for _ in range(24)]
misc          = [1500  + np.random.randint(-300, 300)            for _ in range(24)]

total_burn = [s+i+m+sw+o+misc_ for s,i,m,sw,o,misc_ in
              zip(salaries, infrastructure, marketing, software, office, misc)]

# Revenue (MRR growing with some churn)
mrr = [8000]
for i in range(1, 24):
    growth = np.random.uniform(0.04, 0.12)
    churn  = np.random.uniform(0.01, 0.04)
    mrr.append(int(mrr[-1] * (1 + growth - churn)))

# Cash balance starting at $800k, receiving a $500k raise at month 12
cash = [800000]
raise_event = {12: 500000}
for i in range(1, 24):
    inflow  = mrr[i] + raise_event.get(i, 0)
    outflow = total_burn[i]
    cash.append(cash[-1] + inflow - outflow)

monthly_df = pd.DataFrame({
    "date":           months,
    "salaries":       salaries,
    "infrastructure": infrastructure,
    "marketing":      marketing,
    "software":       software,
    "office":         office,
    "misc":           misc,
    "total_burn":     total_burn,
    "mrr":            mrr,
    "cash_balance":   cash,
    "net_burn":       [b - r for b, r in zip(total_burn, mrr)],
    "runway_months":  [round(c / max(nb, 1), 1) for c, nb in
                       zip(cash, [b - r for b, r in zip(total_burn, mrr)])],
})
monthly_df["date"] = monthly_df["date"].dt.strftime("%Y-%m-%d")

# ── Industry benchmarks ───────────────────────────────────────────────────────
benchmarks = {
    "B2B SaaS (Seed)":    {"avg_burn": 52000,  "avg_runway": 18, "avg_mrr_growth": 0.08},
    "B2B SaaS (Series A)":{"avg_burn": 180000, "avg_runway": 24, "avg_mrr_growth": 0.07},
    "Fintech (Seed)":     {"avg_burn": 75000,  "avg_runway": 20, "avg_mrr_growth": 0.09},
    "E-commerce":         {"avg_burn": 40000,  "avg_runway": 15, "avg_mrr_growth": 0.06},
    "Dev Tools":          {"avg_burn": 48000,  "avg_runway": 22, "avg_mrr_growth": 0.10},
}

# ── Investors / stakeholders ──────────────────────────────────────────────────
investors = [
    {"name": "Sequoia Capital",     "amount": 300000, "date": "2023-01-15", "type": "Lead"},
    {"name": "Y Combinator",        "amount": 125000, "date": "2023-01-15", "type": "Program"},
    {"name": "Angel Syndicate",     "amount": 200000, "date": "2023-07-01", "type": "Angel"},
    {"name": "Founders Fund",       "amount": 500000, "date": "2024-01-01", "type": "Bridge"},
]

os.makedirs("data", exist_ok=True)
monthly_df.to_csv("data/financials.csv", index=False)
with open("data/benchmarks.json", "w") as f:
    json.dump(benchmarks, f, indent=2)
with open("data/investors.json", "w") as f:
    json.dump(investors, f, indent=2)

print("✓ Data generated successfully")
print(f"  Monthly records:  {len(monthly_df)}")
print(f"  Final cash:      ${monthly_df['cash_balance'].iloc[-1]:,.0f}")
print(f"  Final MRR:       ${monthly_df['mrr'].iloc[-1]:,.0f}")
print(f"  Final runway:    {monthly_df['runway_months'].iloc[-1]} months")
