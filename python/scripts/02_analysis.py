"""
02_analysis.py  -  GulfMart advanced retail analytics pipeline
Sections: profiling -> validation -> KPIs -> trend/seasonality/YoY -> store performance & root cause
-> store clustering -> product (ABC, Pareto, margin matrix) -> promo/discount & elasticity
-> loss-making diagnostics -> customer (RFM, segments, cohorts) -> basket affinity -> forecast
Outputs: data/processed/*.csv, data/output/*.csv, data/output/insights.json, docs/charts/*.png
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
RAW, PROC, OUT, CH = ROOT / "data/raw", ROOT / "data/processed", ROOT / "data/output", ROOT / "docs/charts"
for d in (PROC, OUT, CH):
    d.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": .25, "font.size": 9})
C = {"navy": "#1f3a5f", "teal": "#2a9d8f", "amber": "#e9a23b", "red": "#c8553d", "grey": "#8a8f98"}
INS = {}   # insights collected for report + dashboard

# ================================================================= 1. LOAD + PROFILE
fs = pd.read_csv(RAW / "fact_sales.csv", parse_dates=["transaction_date"])
st = pd.read_csv(RAW / "dim_store.csv", parse_dates=["opening_date"])
pr = pd.read_csv(RAW / "dim_product.csv")
cu = pd.read_csv(RAW / "dim_customer.csv")
dd = pd.read_csv(RAW / "dim_date.csv", parse_dates=["date"])

profile = pd.DataFrame({
    "table": ["fact_sales", "dim_store", "dim_product", "dim_customer", "dim_date"],
    "rows": [len(fs), len(st), len(pr), len(cu), len(dd)],
    "nulls": [int(x.isna().sum().sum()) for x in (fs, st, pr, cu, dd)],
    "duplicates": [int(fs.duplicated("transaction_id").sum()), int(st.duplicated("store_id").sum()),
                   int(pr.duplicated("product_id").sum()), int(cu.duplicated("customer_id").sum()),
                   int(dd.duplicated("date").sum())],
})

tol = 0.011
checks = {
    "gross_sales = qty*price": (fs.gross_sales - fs.quantity * fs.unit_price).abs().max() <= tol,
    "net_sales = gross*(1-disc)": (fs.net_sales - fs.gross_sales * (1 - fs.discount_pct)).abs().max() <= tol,
    "total_cost = qty*unit_cost": (fs.total_cost - fs.quantity * fs.unit_cost).abs().max() <= tol,
    "gross_profit = net-cost": (fs.gross_profit - (fs.net_sales - fs.total_cost)).abs().max() <= tol,
    "discount_amount = gross-net": (fs.discount_amount - (fs.gross_sales - fs.net_sales)).abs().max() <= tol,
    "FK store valid": fs.store_id.isin(st.store_id).all(),
    "FK product valid": fs.product_id.isin(pr.product_id).all(),
    "FK customer valid": fs.customer_id.isin(cu.customer_id).all(),
    "FK date valid": fs.transaction_date.isin(dd.date).all(),
    "quantity > 0": (fs.quantity > 0).all(),
    "discount in [0, .25]": fs.discount_pct.between(0, .25).all(),
    "no future dates": fs.transaction_date.max() <= pd.Timestamp("2025-12-31"),
}
vtab = pd.DataFrame({"check": checks.keys(), "passed": [bool(v) for v in checks.values()]})
INS["validation"] = {"all_pass": bool(vtab.passed.all()), "n_checks": len(vtab)}
profile.to_csv(OUT / "data_profile.csv", index=False)
vtab.to_csv(OUT / "validation_checks.csv", index=False)

# outliers (IQR on net_sales) - flagged, not removed
q1, q3 = fs.net_sales.quantile([.25, .75])
iqr = q3 - q1
fs["is_outlier"] = fs.net_sales > q3 + 3 * iqr
INS["outlier_share"] = float(fs.is_outlier.mean())

# ================================================================= 2. ENRICH
fs = (fs.merge(st[["store_id", "store_name", "city", "region", "store_type", "store_size_sqft", "target_sales", "target_margin"]], on="store_id")
        .merge(pr[["product_id", "category", "subcategory", "brand"]], on="product_id")
        .merge(cu[["customer_id", "customer_segment", "city"]].rename(columns={"city": "cust_city"}), on="customer_id"))
fs["year"] = fs.transaction_date.dt.year
fs["ym"] = fs.transaction_date.dt.to_period("M").dt.to_timestamp()
fs["promo"] = fs.discount_pct > 0
fs["loss"] = fs.gross_profit < 0
fs = fs.merge(dd[["date", "event", "is_weekend", "day_of_week"]], left_on="transaction_date", right_on="date")
fs.drop(columns="date").to_csv(PROC / "fact_sales_enriched.csv", index=False)


def kpis(g):
    s = g.net_sales.sum()
    return pd.Series({
        "net_sales": s, "gross_sales": g.gross_sales.sum(), "gross_profit": g.gross_profit.sum(),
        "gm_pct": g.gross_profit.sum() / s, "transactions": len(g), "units": g.quantity.sum(),
        "atv": s / len(g), "upt": g.quantity.sum() / len(g),
        "discount_rate": g.discount_amount.sum() / g.gross_sales.sum(),
        "promo_penetration": g.promo.mean(), "loss_tx_pct": g.loss.mean(),
        "profit_per_tx": g.gross_profit.sum() / len(g),
    })


total = kpis(fs)
by_year = fs.groupby("year").apply(kpis, include_groups=False)
by_year["net_sales_yoy"] = by_year.net_sales.pct_change()
by_year["gp_yoy"] = by_year.gross_profit.pct_change()
INS["kpi_total"] = total.round(4).to_dict()
INS["kpi_year"] = by_year.round(4).reset_index().to_dict("records")
by_year.to_csv(OUT / "kpi_by_year.csv")

# ================================================================= 3. TREND & SEASONALITY
monthly = fs.groupby("ym").apply(kpis, include_groups=False)
monthly["ma3"] = monthly.net_sales.rolling(3).mean()
monthly.to_csv(OUT / "kpi_monthly.csv")
# Seasonality index = month avg / overall avg (de-trended by year mean)
mm = monthly.reset_index()
mm["year"], mm["month"] = mm.ym.dt.year, mm.ym.dt.month
mm["idx"] = mm.net_sales / mm.groupby("year").net_sales.transform("mean")
season_idx = mm.groupby("month").idx.mean().round(3)
INS["seasonality_index"] = season_idx.to_dict()
ev = fs.groupby("event").agg(days=("transaction_date", "nunique"), net=("net_sales", "sum"), tx=("transaction_id", "count"),
                             disc=("discount_amount", "sum"), gross=("gross_sales", "sum"), gp=("gross_profit", "sum"))
ev["sales_per_day"] = ev.net / ev.days
base = ev.loc["No Event", "sales_per_day"]
ev["uplift_vs_base"] = ev.sales_per_day / base - 1
ev["gm_pct"] = ev.gp / ev.net
ev["discount_rate"] = ev.disc / ev.gross
ev.round(4).to_csv(OUT / "event_uplift.csv")
INS["events"] = ev.round(4).reset_index().to_dict("records")
dow = fs.groupby("day_of_week").agg(net=("net_sales", "sum"), days=("transaction_date", "nunique"))
dow["per_day"] = dow.net / dow.days
INS["weekday_profile"] = (dow.per_day / dow.per_day.mean()).round(3).to_dict()

fig, ax = plt.subplots(figsize=(9, 3.6))
ax.plot(monthly.index, monthly.net_sales / 1e3, color=C["navy"], lw=1.6, label="Net sales")
ax.plot(monthly.index, monthly.ma3 / 1e3, color=C["amber"], lw=1.4, ls="--", label="3-mo avg")
ax.set_title("Monthly net sales (SAR thousands)"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(CH / "01_monthly_sales.png"); plt.close()

# ================================================================= 4. STORE PERFORMANCE
latest = fs[fs.year == 2025]
sk = latest.groupby("store_id").apply(kpis, include_groups=False).join(st.set_index("store_id")[
    ["store_name", "city", "region", "store_type", "store_size_sqft", "target_sales", "target_margin"]])
sk["sales_vs_target"] = sk.net_sales / sk.target_sales - 1
sk["margin_vs_target_pp"] = (sk.gm_pct - sk.target_margin) * 100
sk["sales_per_sqft"] = sk.net_sales / sk.store_size_sqft
sk["tx_per_sqft"] = sk.transactions / sk.store_size_sqft
sk["rank_sales"] = sk.net_sales.rank(ascending=False).astype(int)
# peer benchmark within store type
for m in ["sales_per_sqft", "atv", "gm_pct", "tx_per_sqft", "discount_rate", "upt"]:
    sk[f"{m}_peer_idx"] = sk[m] / sk.groupby("store_type")[m].transform("median")
sk["gp_per_sqft"] = sk.gross_profit / sk.store_size_sqft
# Four-quadrant action classification
def quad(r):
    s_ok, m_ok = r.sales_vs_target >= 0, r.margin_vs_target_pp >= 0
    return {(True, True): "Star", (True, False): "Volume without margin",
            (False, True): "Profitable but under-selling", (False, False): "Problem store"}[(s_ok, m_ok)]
sk["quadrant"] = sk.apply(quad, axis=1)
sk.round(4).to_csv(OUT / "store_scorecard_2025.csv")
INS["store_quadrants"] = sk.quadrant.value_counts().to_dict()
INS["store_type_2025"] = (sk.groupby("store_type").agg(
    stores=("store_name", "count"), net_sales=("net_sales", "sum"), gross_profit=("gross_profit", "sum"),
    sqft=("store_size_sqft", "sum"), atv=("atv", "mean"), gm=("gm_pct", "mean")).assign(
    sales_per_sqft=lambda d: d.net_sales / d.sqft, gm_pct=lambda d: d.gross_profit / d.net_sales).round(3)
    .reset_index().to_dict("records"))
# size vs sales correlation
r_size, p_size = stats.pearsonr(np.log(sk.store_size_sqft), np.log(sk.net_sales))
r_spf, _ = stats.spearmanr(sk.store_size_sqft, sk.sales_per_sqft)
INS["size_sales_corr_log"] = {"r": round(float(r_size), 3), "p": float(p_size)}
INS["size_vs_productivity_spearman"] = round(float(r_spf), 3)
INS["top5_stores"] = sk.nlargest(5, "net_sales")[["store_name", "net_sales", "gm_pct"]].round(3).reset_index().to_dict("records")
INS["bottom5_stores"] = sk.nsmallest(5, "sales_per_sqft")[["store_name", "store_type", "sales_per_sqft", "gm_pct"]].round(3).reset_index().to_dict("records")

# Root cause: decompose store gap vs peer median in sales/sqft into traffic and basket effects
sk["traffic_effect"] = np.log(sk.tx_per_sqft_peer_idx)
sk["basket_effect"] = np.log(sk.atv_peer_idx)
sk["gap_total"] = np.log(sk.sales_per_sqft_peer_idx)
def cause(r):
    if r.gap_total >= -0.05:
        return "On/above peer"
    return "Traffic-driven" if abs(r.traffic_effect) > abs(r.basket_effect) else "Basket-driven"
sk["sales_gap_driver"] = sk.apply(cause, axis=1)
INS["sales_gap_drivers"] = sk.sales_gap_driver.value_counts().to_dict()
# Margin root cause: discount depth/penetration vs mix
mix = latest.groupby(["store_id", "category"]).net_sales.sum().unstack(fill_value=0)
mix = mix.div(mix.sum(axis=1), axis=0)
cat_margin = latest.groupby("category").apply(lambda g: g.gross_profit.sum() / g.net_sales.sum(), include_groups=False)
sk["mix_margin_expected"] = (mix * cat_margin).sum(axis=1)
sk["mix_effect_pp"] = (sk.mix_margin_expected - sk.mix_margin_expected.mean()) * 100
sk["promo_effect_pp"] = (sk.gm_pct - sk.mix_margin_expected) * 100
sk.round(4).to_csv(OUT / "store_root_cause_2025.csv")

fig, ax = plt.subplots(figsize=(7, 5))
col = {"Star": C["teal"], "Volume without margin": C["amber"], "Profitable but under-selling": C["navy"], "Problem store": C["red"]}
for q, g in sk.groupby("quadrant"):
    ax.scatter(g.sales_vs_target * 100, g.margin_vs_target_pp, s=np.sqrt(g.net_sales) / 8, c=col[q], alpha=.8, label=q, edgecolor="white")
ax.axhline(0, color="k", lw=.6); ax.axvline(0, color="k", lw=.6)
ax.set_xlabel("Sales vs target (%)"); ax.set_ylabel("Margin vs target (pp)"); ax.set_title("Store action matrix, 2025")
ax.legend(frameon=False, fontsize=7); fig.tight_layout(); fig.savefig(CH / "02_store_matrix.png"); plt.close()

# ================================================================= 5. STORE CLUSTERING
feat = sk[["sales_per_sqft", "atv", "gm_pct", "tx_per_sqft", "discount_rate", "upt"]]
Z = StandardScaler().fit_transform(feat)
inertia = {k: KMeans(k, n_init=10, random_state=1).fit(Z).inertia_ for k in range(2, 7)}
km = KMeans(4, n_init=20, random_state=1).fit(Z)
sk["cluster"] = km.labels_
cprof = sk.groupby("cluster")[list(feat.columns) + ["store_size_sqft"]].mean().round(3)
cprof["stores"] = sk.groupby("cluster").size()
cprof["type_mix"] = sk.groupby("cluster").store_type.agg(lambda s: ", ".join(f"{k}:{v}" for k, v in s.value_counts().items()))
cprof.to_csv(OUT / "store_clusters.csv")
sk[["store_name", "store_type", "cluster"]].to_csv(OUT / "store_cluster_assignment.csv")
INS["clusters"] = cprof.reset_index().to_dict("records")

# ================================================================= 6. PRODUCT ANALYTICS
pk = fs.groupby(["product_id"]).agg(net_sales=("net_sales", "sum"), gp=("gross_profit", "sum"), units=("quantity", "sum"),
                                    tx=("transaction_id", "count"), disc=("discount_amount", "sum"), gross=("gross_sales", "sum"),
                                    loss_tx=("loss", "sum"), promo_share=("promo", "mean")).join(pr.set_index("product_id"))
pk["gm_pct"] = pk.gp / pk.net_sales
pk["discount_rate"] = pk.disc / pk.gross
pk = pk.sort_values("net_sales", ascending=False)
pk["cum_share"] = pk.net_sales.cumsum() / pk.net_sales.sum()
pk["abc"] = np.where(pk.cum_share <= .70, "A", np.where(pk.cum_share <= .90, "B", "C"))
# XYZ on monthly demand variability
mdem = fs.groupby(["product_id", "ym"]).quantity.sum().unstack(fill_value=0)
pk["cv"] = (mdem.std(axis=1) / mdem.mean(axis=1)).reindex(pk.index)
pk["xyz"] = np.where(pk.cv <= .5, "X", np.where(pk.cv <= 1.0, "Y", "Z"))
pk["abc_xyz"] = pk.abc + pk.xyz
# demand vs margin matrix (units median/ margin median)
mu, mg = pk.units.median(), pk.gm_pct.median()
pk["matrix"] = np.select([(pk.units >= mu) & (pk.gm_pct >= mg), (pk.units >= mu) & (pk.gm_pct < mg), (pk.units < mu) & (pk.gm_pct >= mg)],
                         ["Stars", "Traffic drivers (low margin)", "Niche (high margin)"], "Review / rationalise")
pk.round(4).to_csv(OUT / "product_scorecard.csv")
INS["abc"] = pk.groupby("abc").agg(skus=("net_sales", "size"), sales=("net_sales", "sum")).assign(
    sales_share=lambda d: d.sales / d.sales.sum()).round(3).reset_index().to_dict("records")
INS["pareto_20pct_skus_share"] = round(float(pk.net_sales.head(int(len(pk) * .2)).sum() / pk.net_sales.sum()), 3)
INS["product_matrix"] = pk.matrix.value_counts().to_dict()
cat = fs.groupby("category").apply(kpis, include_groups=False)
cat["sales_share"] = cat.net_sales / cat.net_sales.sum()
cat["profit_share"] = cat.gross_profit / cat.gross_profit.sum()
cat["profit_minus_sales_share_pp"] = (cat.profit_share - cat.sales_share) * 100
cat.round(4).to_csv(OUT / "category_kpis.csv")
INS["category"] = cat.round(4).reset_index().to_dict("records")
INS["top_products"] = pk.head(8)[["product_name", "category", "net_sales", "gm_pct"]].round(3).reset_index().to_dict("records")
INS["traffic_drivers_loss"] = pk[pk.matrix.str.startswith("Traffic")].nsmallest(8, "gp")[["product_name", "category", "net_sales", "gp", "gm_pct"]].round(3).reset_index().to_dict("records")

# store x category index (assortment gaps): share vs company share
sc = fs.groupby(["store_type", "category"]).net_sales.sum().unstack(fill_value=0)
sc_share = sc.div(sc.sum(axis=1), axis=0)
sc_share.round(4).to_csv(OUT / "store_type_category_mix.csv")

# ================================================================= 7. PROMOTION & DISCOUNT
disc = fs.groupby("discount_pct").agg(tx=("transaction_id", "count"), units=("quantity", "mean"), atv=("net_sales", "mean"),
                                      gp=("gross_profit", "sum"), net=("net_sales", "sum"), loss_rate=("loss", "mean"),
                                      gp_tx=("gross_profit", "mean"), disc_cost=("discount_amount", "sum"))
disc["gm_pct"] = disc.gp / disc.net
disc.round(4).to_csv(OUT / "discount_ladder.csv")
INS["discount_ladder"] = disc.round(4).reset_index().to_dict("records")

# Uplift: units per tx for promo vs non-promo within same product (controls for product mix)
pp = fs.groupby(["product_id", "promo"]).quantity.mean().unstack()
pp = pp.dropna()
lift = (pp[True] / pp[False] - 1)
INS["units_lift_promo_vs_base_median"] = round(float(lift.median()), 4)
t_stat, p_val = stats.ttest_rel(pp[True], pp[False])
INS["units_lift_ttest_p"] = float(p_val)
# Promo ROI: incremental gross profit vs margin given away
promo_tx = fs[fs.promo]
base_units = promo_tx.product_id.map(pp[False]).fillna(promo_tx.quantity.mean())
promo_tx = promo_tx.assign(base_units=base_units)
promo_tx["incr_units"] = (promo_tx.quantity - promo_tx.base_units).clip(lower=0)
unit_gp_full = (promo_tx.gross_sales / promo_tx.quantity) - promo_tx.unit_cost
promo_tx["margin_given_away"] = promo_tx.discount_amount
promo_tx["incremental_gp"] = promo_tx.incr_units * (promo_tx.net_sales / promo_tx.quantity - promo_tx.unit_cost)
roi = promo_tx.groupby("discount_pct").agg(given_away=("margin_given_away", "sum"), incr_gp=("incremental_gp", "sum"))
roi["net_promo_value"] = roi.incr_gp - roi.given_away
roi["roi"] = roi.net_promo_value / roi.given_away
roi.round(3).to_csv(OUT / "promo_roi.csv")
INS["promo_roi"] = roi.round(3).reset_index().to_dict("records")
# promo by store type, category
pst = fs.groupby("store_type").apply(lambda g: pd.Series({"promo_penetration": g.promo.mean(), "discount_rate": g.discount_amount.sum() / g.gross_sales.sum(),
                                                         "gm_pct": g.gross_profit.sum() / g.net_sales.sum(), "loss_tx_pct": g.loss.mean()}), include_groups=False)
pst.round(4).to_csv(OUT / "promo_by_store_type.csv"); INS["promo_by_type"] = pst.round(4).reset_index().to_dict("records")
pcat = fs.groupby("category").apply(lambda g: pd.Series({"promo_penetration": g.promo.mean(), "discount_rate": g.discount_amount.sum() / g.gross_sales.sum(),
                                                        "loss_tx_pct": g.loss.mean(), "gm_promo": g[g.promo].gross_profit.sum() / g[g.promo].net_sales.sum(),
                                                        "gm_nonpromo": g[~g.promo].gross_profit.sum() / g[~g.promo].net_sales.sum()}), include_groups=False)
pcat["margin_dilution_pp"] = (pcat.gm_promo - pcat.gm_nonpromo) * 100
pcat.round(4).to_csv(OUT / "promo_by_category.csv"); INS["promo_by_category"] = pcat.round(4).reset_index().to_dict("records")
# Break-even discount per product: d* = 1 - cost/price  (below this discount = still profitable)
pr["breakeven_discount"] = (1 - pr.unit_cost / pr.selling_price).round(4)
pr["max_safe_discount_tier"] = pd.cut(pr.breakeven_discount, [-1, .05, .10, .15, .20, .25, 1], labels=["0%", "5%", "10%", "15%", "20%", "25%"]).astype(str)
pr.to_csv(OUT / "product_breakeven_discount.csv", index=False)
INS["skus_unsafe_at_25"] = int((pr.breakeven_discount < .25).sum())
INS["skus_unsafe_at_20"] = int((pr.breakeven_discount < .20).sum())

# ================================================================= 8. LOSS-MAKING DIAGNOSTICS
ls = fs[fs.loss]
INS["loss"] = {"tx": int(len(ls)), "pct": round(float(fs.loss.mean()), 4), "total_loss": round(float(ls.gross_profit.sum()), 2),
               "share_of_promo_tx": round(float(ls.shape[0] / fs.promo.sum()), 4),
               "share_at_20_25": round(float(ls.discount_pct.ge(.20).mean()), 3)}
INS["loss_by_category"] = ls.groupby("category").agg(tx=("loss", "size"), loss=("gross_profit", "sum")).round(0).sort_values("loss").reset_index().to_dict("records")
INS["loss_by_store_type"] = ls.groupby("store_type").agg(tx=("loss", "size"), loss=("gross_profit", "sum")).round(0).reset_index().to_dict("records")
loss_sku = ls.groupby("product_id").agg(loss_tx=("loss", "size"), loss=("gross_profit", "sum")).join(pr.set_index("product_id")[["product_name", "category", "breakeven_discount"]])
loss_sku.sort_values("loss").head(25).round(2).to_csv(OUT / "top_loss_skus.csv")
INS["loss_sku_concentration_top20_share"] = round(float(loss_sku.loss.nsmallest(20).sum() / loss_sku.loss.sum()), 3)
# What-if: cap discount at product break-even tier => recovered loss
fs["cap"] = np.minimum(fs.discount_pct, np.floor(fs.product_id.map(pr.set_index("product_id").breakeven_discount) * 20) / 20)
fs["net_sales_cap"] = fs.gross_sales * (1 - fs.cap)
fs["gp_cap"] = fs.net_sales_cap - fs.total_cost
INS["whatif_cap"] = {"gp_current": round(float(fs.gross_profit.sum()), 0), "gp_capped_no_volume_loss": round(float(fs.gp_cap.sum()), 0),
                     "gp_uplift_abs": round(float(fs.gp_cap.sum() - fs.gross_profit.sum()), 0),
                     "gp_uplift_pct": round(float(fs.gp_cap.sum() / fs.gross_profit.sum() - 1), 4)}
# conservative scenario: lose 30% of the volume on transactions where cap binds
bound = fs.cap < fs.discount_pct
gp_cons = np.where(bound, 0.7 * fs.gp_cap + 0.3 * 0, fs.gp_cap)
gp_cons = np.where(bound, 0.7 * fs.gp_cap, fs.gross_profit)
INS["whatif_cap"]["gp_capped_30pct_volume_loss_on_capped_tx"] = round(float(gp_cons.sum()), 0)
INS["whatif_cap"]["gp_uplift_conservative"] = round(float(gp_cons.sum() - fs.gross_profit.sum()), 0)

fig, ax = plt.subplots(figsize=(6, 3.4))
ax.bar((disc.index * 100).astype(int).astype(str) + "%", disc.gm_pct * 100, color=[C["navy"]] + [C["amber"]] * 3 + [C["red"]] * 2)
ax.set_title("Gross margin % by discount level"); fig.tight_layout(); fig.savefig(CH / "03_margin_by_discount.png"); plt.close()

# ================================================================= 9. CUSTOMER ANALYTICS
snap = fs.transaction_date.max() + pd.Timedelta(days=1)
rfm = fs.groupby("customer_id").agg(recency=("transaction_date", lambda d: (snap - d.max()).days), frequency=("transaction_id", "count"),
                                    monetary=("net_sales", "sum"), gp=("gross_profit", "sum"), promo_share=("promo", "mean"),
                                    first=("transaction_date", "min"))
rfm["R"] = pd.qcut(rfm.recency.rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm.frequency.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["M"] = pd.qcut(rfm.monetary.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
def seg(r):
    if r.R >= 4 and r.F >= 4 and r.M >= 4: return "Champions"
    if r.R >= 3 and r.F >= 3: return "Loyal"
    if r.R >= 4 and r.F <= 2: return "New / Promising"
    if r.R <= 2 and r.F >= 4: return "At risk (high value)"
    if r.R <= 2 and r.F <= 2: return "Lapsed"
    return "Needs attention"
rfm["rfm_segment"] = rfm.apply(seg, axis=1)
rfm = rfm.join(cu.set_index("customer_id")[["customer_segment", "city", "age", "gender"]])
rfm.to_csv(OUT / "customer_rfm.csv", float_format="%.3f")
rs = rfm.groupby("rfm_segment").agg(customers=("frequency", "size"), net_sales=("monetary", "sum"), gp=("gp", "sum"),
                                    avg_freq=("frequency", "mean"), avg_recency=("recency", "mean")).assign(
    sales_share=lambda d: d.net_sales / d.net_sales.sum(), cust_share=lambda d: d.customers / d.customers.sum()).round(3)
rs.to_csv(OUT / "rfm_segments.csv"); INS["rfm"] = rs.reset_index().to_dict("records")
cs = fs.groupby("customer_segment").apply(kpis, include_groups=False)
cs["customers"] = fs.groupby("customer_segment").customer_id.nunique()
cs["sales_per_customer"] = cs.net_sales / cs.customers
cs.round(4).to_csv(OUT / "customer_segment_kpis.csv"); INS["cust_segment"] = cs.round(4).reset_index().to_dict("records")
# concentration
cust_sorted = rfm.monetary.sort_values(ascending=False)
INS["top10pct_customers_sales_share"] = round(float(cust_sorted.head(int(len(cust_sorted) * .1)).sum() / cust_sorted.sum()), 3)
g = (cust_sorted.cumsum() / cust_sorted.sum()).values
lorenz = np.concatenate([[0], np.sort(rfm.monetary.values).cumsum() / rfm.monetary.sum()])
INS["customer_gini"] = round(float(1 - 2 * np.trapezoid(lorenz, dx=1 / len(rfm.monetary))), 3)
# promo dependence: customers where >50% tx on promo
rfm["promo_dependent"] = rfm.promo_share > .5
INS["promo_dependent_customers_pct"] = round(float(rfm.promo_dependent.mean()), 3)
INS["promo_dependent_gp_share"] = round(float(rfm[rfm.promo_dependent].gp.sum() / rfm.gp.sum()), 3)
# cohort retention (acquisition = first purchase quarter)
fs["cohort"] = fs.customer_id.map(rfm["first"]).dt.to_period("Q")
fs["q"] = fs.transaction_date.dt.to_period("Q")
coh = fs.groupby(["cohort", "q"]).customer_id.nunique().unstack()
coh_ret = coh.div(np.diag(coh.reindex(columns=coh.index).values) if False else coh.apply(lambda r: r.dropna().iloc[0], axis=1), axis=0)
coh_ret.round(3).to_csv(OUT / "cohort_retention.csv")
active_q = fs.groupby("q").customer_id.nunique()
INS["active_customers_by_quarter"] = {str(k): int(v) for k, v in active_q.items()}
# repeat rate / CLV (simple: avg GP per customer per year * expected lifetime from churn)
yr_act = fs.groupby(["year"]).customer_id.nunique()
cust_year = fs.groupby("customer_id").year.agg(lambda s: set(s))
ret_23_24 = np.mean([2024 in y for y in cust_year if 2023 in y])
ret_24_25 = np.mean([2025 in y for y in cust_year if 2024 in y])
INS["annual_retention"] = {"2023_to_2024": round(float(ret_23_24), 3), "2024_to_2025": round(float(ret_24_25), 3)}
gp_cust_yr = rfm.gp.sum() / len(rfm) / 3
churn = 1 - ret_24_25
INS["clv_simple"] = {"gp_per_customer_year": round(float(gp_cust_yr), 2), "lifetime_years_capped_5": round(float(min(1 / churn, 5)), 2),
                     "clv_5yr_cap": round(float(gp_cust_yr * min(1 / churn, 5)), 2)}
city = fs.groupby("city").apply(kpis, include_groups=False)[["net_sales", "gross_profit", "gm_pct", "atv", "transactions"]].round(3)
city.to_csv(OUT / "city_kpis.csv"); INS["city"] = city.reset_index().to_dict("records")

# ================================================================= 10. BASKET AFFINITY (customer-store-day)
b = fs.groupby(["customer_id", "store_id", "transaction_date"]).product_id.apply(lambda s: sorted(set(s)))
b = b[b.map(len) >= 2]
cats_b = fs.groupby(["customer_id", "store_id", "transaction_date"]).subcategory.apply(lambda s: sorted(set(s)))
n_baskets = fs.groupby(["customer_id", "store_id", "transaction_date"]).ngroups
multi = cats_b[cats_b.map(len) >= 2]
from itertools import combinations
from collections import Counter
pair, single = Counter(), Counter()
for items in cats_b:
    single.update(items)
    pair.update(combinations(items, 2))
rows = []
for (a, c), n in pair.items():
    supp = n / n_baskets
    conf = n / single[a]
    lift_ = conf / (single[c] / n_baskets)
    rows.append((a, c, n, supp, conf, lift_))
aff = pd.DataFrame(rows, columns=["item_a", "item_b", "baskets", "support", "confidence", "lift"])
aff = aff[aff.baskets >= 30].sort_values("lift", ascending=False)
aff.round(4).head(40).to_csv(OUT / "basket_affinity_subcategory.csv", index=False)
INS["basket"] = {"n_visits": int(n_baskets), "multi_item_visit_pct": round(float(len(multi) / n_baskets), 4),
                 "top_pairs": aff.head(5).round(3).to_dict("records")}

# ================================================================= 11. FORECAST (seasonal naive x trend, with holdout backtest)
ms = monthly.net_sales.copy()
def hw_forecast(y, h, period=12, alpha=.3, beta=.05, gamma=.3):
    y = np.asarray(y, float)
    L = y[:period].mean(); T = (y[period:2 * period].mean() - y[:period].mean()) / period
    S = list(y[:period] / L)
    for t in range(len(y)):
        s = S[t % period] if t < period else S[-period]
        prevL = L
        L = alpha * y[t] / s + (1 - alpha) * (L + T)
        T = beta * (L - prevL) + (1 - beta) * T
        S.append(gamma * y[t] / L + (1 - gamma) * s)
    return np.array([(L + (i + 1) * T) * S[-period + (i % period)] for i in range(h)])
# backtest: train on first 30 months, predict last 6
train, test = ms.iloc[:30], ms.iloc[30:]
bt = hw_forecast(train.values, 6)
mape = float(np.mean(np.abs(bt - test.values) / test.values))
snaive = ms.iloc[18:24].values * (ms.iloc[24:30].mean() / ms.iloc[12:18].mean())
mape_naive = float(np.mean(np.abs(snaive - test.values) / test.values))
fc = hw_forecast(ms.values, 12)
fidx = pd.date_range(ms.index[-1] + pd.offsets.MonthBegin(1), periods=12, freq="MS")
resid_sd = float(np.std(bt - test.values))
fdf = pd.DataFrame({"month": fidx, "forecast": fc, "lo80": fc - 1.28 * resid_sd, "hi80": fc + 1.28 * resid_sd})
fdf.round(0).to_csv(OUT / "forecast_2026.csv", index=False)
INS["forecast"] = {"backtest_mape_holt_winters": round(mape, 4), "backtest_mape_seasonal_naive": round(mape_naive, 4),
                   "fy2026_net_sales": round(float(fc.sum()), 0), "growth_vs_2025": round(float(fc.sum() / ms.iloc[-12:].sum() - 1), 4),
                   "monthly": fdf.assign(month=fdf.month.dt.strftime("%Y-%m")).round(0).to_dict("records")}
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.plot(ms.index, ms / 1e3, color=C["navy"], label="Actual")
ax.plot(fdf.month, fdf.forecast / 1e3, color=C["teal"], label="Forecast 2026")
ax.fill_between(fdf.month, fdf.lo80 / 1e3, fdf.hi80 / 1e3, color=C["teal"], alpha=.2, label="80% band")
ax.set_title("Net sales forecast, Holt-Winters (SAR thousands)"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(CH / "04_forecast.png"); plt.close()

# ================================================================= 12. SUPPORTING CHARTS
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
s_sorted = sk.sort_values("net_sales")
axs[0].barh(s_sorted.store_name.str.replace("GulfMart ", ""), s_sorted.net_sales / 1e3, color=[col[q] for q in s_sorted.quadrant])
axs[0].set_title("2025 net sales by store (SAR k)"); axs[0].tick_params(axis="y", labelsize=6)
axs[1].scatter(sk.store_size_sqft / 1e3, sk.sales_per_sqft, c=[col[q] for q in sk.quadrant], s=40)
axs[1].set_xlabel("Store size (k sqft)"); axs[1].set_ylabel("Sales per sqft"); axs[1].set_title("Size vs productivity")
fig.tight_layout(); fig.savefig(CH / "05_store_sales.png"); plt.close()

fig, ax = plt.subplots(figsize=(6, 3.4))
ax.plot(np.arange(1, len(pk) + 1), pk.cum_share * 100, color=C["navy"])
ax.axhline(70, ls=":", color=C["grey"]); ax.axhline(90, ls=":", color=C["grey"])
ax.set_xlabel("SKUs ranked by sales"); ax.set_ylabel("Cumulative % of sales"); ax.set_title("Product Pareto curve")
fig.tight_layout(); fig.savefig(CH / "06_pareto.png"); plt.close()

# ================================================================= EXPORT
def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, (pd.Timestamp,)): return str(o.date())
    return o
INS["store_table"] = clean(sk.round(4).reset_index().to_dict("records"))
INS["monthly"] = clean(monthly.round(2).reset_index().assign(ym=lambda d: d.ym.dt.strftime("%Y-%m")).to_dict("records"))
json.dump(clean(INS), open(OUT / "insights.json", "w"), indent=1, default=str)
print("Done. Validation:", INS["validation"])
print(json.dumps({k: INS[k] for k in ["kpi_total", "loss", "whatif_cap", "forecast"] if k in INS}, indent=1, default=str)[:3500])
