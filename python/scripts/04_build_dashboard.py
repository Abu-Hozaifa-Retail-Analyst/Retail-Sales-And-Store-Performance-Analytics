"""04_build_dashboard.py - bakes insights.json into a self-contained HTML dashboard (powerbi/ folder holds the .pbix spec; this is the web preview)."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
I = json.load(open(ROOT / "data/output/insights.json"))
r = lambda x, n=0: round(x, n)
D = {
 "kpi": {y["year"]: {k: y[k] for k in ("net_sales", "gross_profit", "gm_pct", "transactions", "atv", "discount_rate", "net_sales_yoy")} for y in I["kpi_year"]},
 "monthly": [[m["ym"], r(m["net_sales"])] for m in I["monthly"]],
 "fc": [[m["month"], m["forecast"], m["lo80"], m["hi80"]] for m in I["forecast"]["monthly"]],
 "stores": [[s["store_name"].replace("GulfMart ", ""), s["store_type"], r(s["net_sales"]), r(s["sales_vs_target"] * 100, 1), r(s["margin_vs_target_pp"], 1),
             r(s["sales_per_sqft"], 1), s["quadrant"], r(s["gm_pct"] * 100, 1), r(s["sales_per_sqft_peer_idx"], 2)] for s in I["store_table"]],
 "cat": [[c["category"], r(c["sales_share"] * 100, 1), r(c["profit_share"] * 100, 1), r(c["gm_pct"] * 100, 1), r(c["loss_tx_pct"] * 100, 1)] for c in I["category"]],
 "disc": [[int(d["discount_pct"] * 100), r(d["gm_pct"] * 100, 1), r(d["units"], 2), r(d["loss_rate"] * 100, 1)] for d in I["discount_ladder"]],
 "scen": [[s["scenario"], r(s["gp_delta"]), r(s["gp_delta_pct"] * 100, 1), r(s["gm_pct"] * 100, 1)] for s in I["scenarios"][1:]],
 "ev": [[e["event"].replace("_", " "), r(e["uplift_vs_base"] * 100), r(e["gm_pct"] * 100, 1)] for e in I["events"] if e["event"] != "No Event"],
 "rfm": [[x["rfm_segment"], r(x["cust_share"] * 100, 1), r(x["sales_share"] * 100, 1)] for x in sorted(I["rfm"], key=lambda z: -z["sales_share"])],
 "fy26": [I["forecast"]["fy2026_net_sales"], r(I["forecast"]["growth_vs_2025"] * 100, 1), r(I["forecast"]["backtest_mape_holt_winters"] * 100, 1)],
}
html = open(ROOT / "powerbi/dashboard_template.html").read().replace("/*DATA*/", "const D=" + json.dumps(D, separators=(",", ":")) + ";")
(ROOT / "powerbi/gulfmart_dashboard.html").write_text(html)
print(len(html) // 1024, "KB")
