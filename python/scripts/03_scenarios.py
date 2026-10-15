"""
03_scenarios.py - what-if models on the enriched fact table (uses category elasticities estimated from data).
Scenarios: (A) cap discount depth at X%; (B) remove promos on Electronics; (C) Ramadan/White Friday only deep promos.
Units respond via estimated elasticity e_c: units_new = units * (1 + e_c*d_new) / (1 + e_c*d_old).
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
fs = pd.read_csv(ROOT / "data/processed/fact_sales_enriched.csv", parse_dates=["transaction_date"])
fs = fs[fs.year == 2025].copy()

# 1) estimate elasticity per category: log-linear regression of units on discount depth, controlling for product
est = {}
for c, g in fs.groupby("category"):
    g = g.assign(y=np.log(g.quantity), pid=g.product_id.astype("category").cat.codes)
    y = g.y - g.groupby("pid").y.transform("mean"); x = g.discount_pct - g.groupby("pid").discount_pct.transform("mean")
    est[c] = float((x * y).sum() / (x * x).sum())   # semi-elasticity: %units per 1.00 of discount

def run(disc_new, label):
    d_old = fs.discount_pct.values
    e = fs.category.map(est).values
    q_new = fs.quantity.values * np.exp(e * (disc_new - d_old))
    net = q_new * fs.unit_price.values * (1 - disc_new)
    gp = net - q_new * fs.unit_cost.values
    return {"scenario": label, "net_sales": float(net.sum()), "gross_profit": float(gp.sum()),
            "gm_pct": float(gp.sum() / net.sum()), "units": float(q_new.sum())}

base = run(fs.discount_pct.values, "Baseline 2025")
res = [base]
for cap in (0.20, 0.15, 0.10):
    res.append(run(np.minimum(fs.discount_pct.values, cap), f"Cap discount at {int(cap*100)}%"))
res.append(run(np.where(fs.category == "Electronics", 0, fs.discount_pct.values), "No promo on Electronics"))
combo = np.where(fs.category == "Electronics", 0, np.minimum(fs.discount_pct.values, 0.15))
res.append(run(combo, "Cap 15% + no Electronics promo"))
ev_deep = fs.event.isin(["Ramadan", "White_Friday", "Eid_Fitr"]).values
res.append(run(np.where(ev_deep, fs.discount_pct.values, np.minimum(fs.discount_pct.values, 0.10)), "Deep promo only in peak events (else cap 10%)"))
out = pd.DataFrame(res)
out["gp_delta"] = out.gross_profit - base["gross_profit"]; out["gp_delta_pct"] = out.gp_delta / base["gross_profit"]
out["sales_delta_pct"] = out.net_sales / base["net_sales"] - 1
out.round(4).to_csv(ROOT / "data/output/promo_scenarios_2025.csv", index=False)
pd.Series(est).round(3).rename("semi_elasticity").to_csv(ROOT / "data/output/estimated_elasticity.csv")
I = json.load(open(ROOT / "data/output/insights.json")); I["scenarios"] = out.round(4).to_dict("records"); I["elasticity"] = {k: round(v, 3) for k, v in est.items()}
json.dump(I, open(ROOT / "data/output/insights.json", "w"), indent=1)
print(out.round(3).to_string()); print(pd.Series(est).round(2))
