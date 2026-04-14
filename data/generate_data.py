import pandas as pd
import numpy as np
from datetime import datetime
import json, os

np.random.seed(42)

# ── 24 months — company that's challenged but alive ───────────────────────────
months = pd.date_range(start="2023-01-01", periods=24, freq="MS")

salaries       = [32000 + i*600  + np.random.randint(-400,400)  for i in range(24)]
infrastructure = [3200  + i*80   + np.random.randint(-150,150)  for i in range(24)]
marketing      = [4500  + i*200  + np.random.randint(-500,500)  for i in range(24)]
software       = [2200  + i*40   + np.random.randint(-80,80)    for i in range(24)]
office         = [2800  + np.random.randint(-80,80)             for _ in range(24)]
misc           = [1200  + np.random.randint(-200,200)           for _ in range(24)]

total_burn = [s+i+m+sw+o+ms for s,i,m,sw,o,ms in
              zip(salaries,infrastructure,marketing,software,office,misc)]

# MRR: starts $18K, grows 7-11% monthly, realistic SaaS
mrr = [18000]
for i in range(1, 24):
    growth = np.random.uniform(0.06, 0.11)
    churn  = np.random.uniform(0.01, 0.03)
    mrr.append(int(mrr[-1] * (1 + growth - churn)))

# Funding events: seed $600K at month 0, Series bridge $400K at month 14
funding = {0: 600000, 14: 400000}

cash = [600000]
for i in range(1, 24):
    inflow  = mrr[i] + funding.get(i, 0)
    outflow = total_burn[i]
    cash.append(cash[-1] + inflow - outflow)

net_burn     = [b - r for b, r in zip(total_burn, mrr)]
runway_months= [round(c / max(nb,1), 1) if nb > 0 else 99.0
                for c, nb in zip(cash, net_burn)]

monthly_df = pd.DataFrame({
    "date":           [m.strftime("%Y-%m-%d") for m in months],
    "salaries":       salaries,
    "infrastructure": infrastructure,
    "marketing":      marketing,
    "software":       software,
    "office":         office,
    "misc":           misc,
    "total_burn":     total_burn,
    "mrr":            mrr,
    "cash_balance":   cash,
    "net_burn":       net_burn,
    "runway_months":  runway_months,
})

benchmarks = {
    "B2B SaaS (Seed)":    {"avg_burn": 52000,  "avg_runway": 18, "avg_mrr_growth": 0.08},
    "B2B SaaS (Series A)":{"avg_burn": 180000, "avg_runway": 24, "avg_mrr_growth": 0.07},
    "Fintech (Seed)":     {"avg_burn": 75000,  "avg_runway": 20, "avg_mrr_growth": 0.09},
    "E-commerce":         {"avg_burn": 40000,  "avg_runway": 15, "avg_mrr_growth": 0.06},
    "Dev Tools":          {"avg_burn": 48000,  "avg_runway": 22, "avg_mrr_growth": 0.10},
}

investors = [
    {"name": "Sequoia Capital",  "amount": 300000, "date": "2023-01-15", "type": "Lead"},
    {"name": "Y Combinator",     "amount": 125000, "date": "2023-01-15", "type": "Program"},
    {"name": "Angel Syndicate",  "amount": 175000, "date": "2023-01-15", "type": "Angel"},
    {"name": "Founders Fund",    "amount": 400000, "date": "2024-03-01", "type": "Bridge"},
]

os.makedirs("data", exist_ok=True)
monthly_df.to_csv("data/financials.csv", index=False)
with open("data/benchmarks.json","w") as f: json.dump(benchmarks, f, indent=2)
with open("data/investors.json","w")  as f: json.dump(investors,  f, indent=2)

latest = monthly_df.iloc[-1]
print("✓ Dataset regenerated")
print(f"  Cash balance:   ${latest['cash_balance']:,.0f}")
print(f"  MRR:            ${latest['mrr']:,.0f}")
print(f"  Total burn:     ${latest['total_burn']:,.0f}")
print(f"  Net burn:       ${latest['net_burn']:,.0f}")
print(f"  Runway:         {latest['runway_months']} months")
