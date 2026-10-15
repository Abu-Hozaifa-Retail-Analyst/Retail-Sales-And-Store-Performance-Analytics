"""
01_generate_data.py
GulfMart synthetic retail data generator (star schema).

Follows the repo README spec:
  25 stores (10 Supermarket, 7 Express, 5 Hypermarket, 3 Neighborhood)
  500 products, 5,000 customers, 120,000 transactions, multi-year (2023-2025)
  Assortment by store type: Hyper 90%, Super 75%, Express 45%, Neighborhood 35%
  Promo probability by store type: Hyper 25%, Super 30%, Express 35%, Neighborhood 40%
  Discounts: 5/10/15/20/25%, negative-profit transactions kept on purpose.

All business assumptions below are synthetic and documented for reproducibility.
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
PRICE_SCALE = 1.8   # calibrates ATV so mean gross profit/tx is close to the README (~45 SAR)
QTY_SCALE = 1.5
rng = np.random.default_rng(SEED)
OUT = Path(__file__).resolve().parents[2] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

N_TX, N_PROD, N_CUST = 120_000, 500, 5_000
START, END = "2023-01-01", "2025-12-31"

# ---------------------------------------------------------------- dim_date
dates = pd.date_range(START, END, freq="D")
dim_date = pd.DataFrame({"date": dates})
dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
dim_date["year"] = dim_date["date"].dt.year
dim_date["quarter"] = dim_date["date"].dt.quarter
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.month_name()
dim_date["week"] = dim_date["date"].dt.isocalendar().week.astype(int)
dim_date["day_of_week"] = dim_date["date"].dt.day_name()
# Saudi weekend = Friday/Saturday
dim_date["is_weekend"] = dim_date["day_of_week"].isin(["Friday", "Saturday"]).astype(int)

# Seasonal demand multiplier (approximate Saudi retail calendar, 2023-2025)
# Ramadan, Eid al-Fitr, Eid al-Adha, White Friday (late Nov), National Day (Sep 23), Founding Day (Feb 22)
EVENTS = {
    "Ramadan":     [("2023-03-23", "2023-04-20", 1.35), ("2024-03-11", "2024-04-09", 1.35), ("2025-03-01", "2025-03-29", 1.35)],
    "Eid_Fitr":    [("2023-04-21", "2023-04-25", 1.25), ("2024-04-10", "2024-04-14", 1.25), ("2025-03-30", "2025-04-03", 1.25)],
    "Eid_Adha":    [("2023-06-27", "2023-07-01", 1.20), ("2024-06-15", "2024-06-19", 1.20), ("2025-06-05", "2025-06-09", 1.20)],
    "White_Friday":[("2023-11-20", "2023-11-30", 1.40), ("2024-11-25", "2024-12-01", 1.40), ("2025-11-24", "2025-11-30", 1.40)],
    "National_Day":[("2023-09-21", "2023-09-23", 1.15), ("2024-09-21", "2024-09-23", 1.15), ("2025-09-21", "2025-09-23", 1.15)],
}
dim_date["event"] = "No Event"
dim_date["season_mult"] = 1.0
for ev, spans in EVENTS.items():
    for s, e, m in spans:
        mask = (dim_date["date"] >= s) & (dim_date["date"] <= e)
        dim_date.loc[mask, "event"] = ev
        dim_date.loc[mask, "season_mult"] = m
# summer slowdown (Jul-Aug) and weekend lift, mild growth trend ~6%/yr
summer = dim_date["month"].isin([7, 8]) & (dim_date["event"] == "No Event")
dim_date.loc[summer, "season_mult"] *= 0.88
dim_date.loc[dim_date["is_weekend"] == 1, "season_mult"] *= 1.12
years_from_start = (dim_date["date"] - dim_date["date"].min()).dt.days / 365.0
dim_date["day_weight"] = dim_date["season_mult"] * (1.06 ** years_from_start)

# ---------------------------------------------------------------- dim_store
store_plan = (["Hypermarket"] * 5 + ["Supermarket"] * 10 + ["Express"] * 7 + ["Neighborhood"] * 3)
cities = {
    "Riyadh": "Central", "Jeddah": "Western", "Dammam": "Eastern", "Khobar": "Eastern",
    "Makkah": "Western", "Madinah": "Western", "Abha": "Southern", "Tabuk": "Northern",
    "Buraidah": "Central", "Taif": "Western",
}
city_list = list(cities)
size_range = {"Hypermarket": (60_000, 110_000), "Supermarket": (18_000, 40_000),
              "Express": (3_000, 8_000), "Neighborhood": (1_500, 4_000)}
type_target_per_tx = {"Hypermarket": 1.0, "Supermarket": 1.0, "Express": 1.0, "Neighborhood": 1.0}
rows = []
for i, st in enumerate(store_plan, start=1):
    city = city_list[(i * 3) % len(city_list)] if i > 3 else city_list[i - 1]
    lo, hi = size_range[st]
    size = int(rng.integers(lo, hi))
    open_year = int(rng.integers(2008, 2022))
    rows.append({
        "store_id": i, "store_name": f"GulfMart {city} {st[:3].upper()}-{i:02d}",
        "city": city, "region": cities[city], "store_type": st, "store_size_sqft": size,
        "opening_date": pd.Timestamp(open_year, int(rng.integers(1, 13)), 1).date(),
        # hidden-but-realistic performance factor (not exported) drives volume differences
        "_perf": float(np.clip(rng.normal(1.0, 0.18), 0.6, 1.4)),
    })
dim_store = pd.DataFrame(rows)

# ---------------------------------------------------------------- dim_product
categories = {
    # category: (demand weight, avg cost range, markup range, subcats)
    "Food & Beverages": (0.24, (2, 25), (0.28, 0.48), ["Snacks", "Beverages", "Pantry", "Dairy & Eggs", "Frozen"]),
    "Fresh Food":       (0.18, (3, 30), (0.25, 0.42), ["Fruits", "Vegetables", "Meat & Poultry", "Bakery", "Seafood"]),
    "Household":        (0.14, (4, 45), (0.30, 0.50), ["Cleaning", "Paper Goods", "Kitchenware", "Laundry"]),
    "Personal Care":    (0.12, (3, 40), (0.38, 0.62), ["Hair Care", "Skin Care", "Oral Care", "Hygiene"]),
    "Health & Wellness":(0.09, (5, 70), (0.35, 0.58), ["Vitamins", "OTC", "Fitness Nutrition", "First Aid"]),
    "Baby Care":        (0.09, (6, 80), (0.28, 0.45), ["Diapers", "Baby Food", "Baby Hygiene", "Toys"]),
    "Beauty":           (0.08, (8, 120), (0.48, 0.85), ["Fragrance", "Makeup", "Beauty Tools", "Nail Care"]),
    "Electronics":      (0.06, (25, 600), (0.12, 0.30), ["Accessories", "Small Appliances", "Audio", "Mobile"]),
}
brands = [f"Brand {c}" for c in "ABCDEFGHIJKLMNOPQRST"]
cat_names = list(categories)
# product counts proportional to weights but with a floor
counts = np.maximum(20, np.round(np.array([categories[c][0] for c in cat_names]) * N_PROD)).astype(int)
counts[0] += N_PROD - counts.sum()
prod_rows, pid = [], 1
for c, n in zip(cat_names, counts):
    w, (clo, chi), (mlo, mhi), subs = categories[c]
    costs = np.round(np.exp(rng.uniform(np.log(clo), np.log(chi), n)) * PRICE_SCALE, 2)
    markups = rng.uniform(mlo, mhi, n)
    for k in range(n):
        sub = subs[k % len(subs)]
        prod_rows.append({
            "product_id": pid, "product_name": f"{sub} Item {pid:03d}", "category": c,
            "subcategory": sub, "brand": brands[int(rng.integers(0, len(brands)))],
            "unit_cost": float(costs[k]), "selling_price": round(float(costs[k] * (1 + markups[k])), 2),
        })
        pid += 1
dim_product = pd.DataFrame(prod_rows)
# Pareto-like popularity inside category (a few hero SKUs)
dim_product["_pop"] = rng.pareto(1.6, len(dim_product)) + 0.3
# Assortment depends on store type: each store carries a random subset (stable per store)
assort_p = {"Hypermarket": 0.90, "Supermarket": 0.75, "Express": 0.45, "Neighborhood": 0.35}
assortment = {}
for _, s in dim_store.iterrows():
    assortment[s.store_id] = rng.random(len(dim_product)) < assort_p[s.store_type]
    # Electronics rarely stocked in small formats
    if s.store_type in ("Express", "Neighborhood"):
        elec = (dim_product["category"] == "Electronics").values
        assortment[s.store_id] &= ~(elec & (rng.random(len(dim_product)) < 0.7))

# ---------------------------------------------------------------- dim_customer
segments = ["Budget Shopper", "Regular Family", "Premium", "Occasional"]
seg_p = [0.30, 0.35, 0.15, 0.20]
dim_customer = pd.DataFrame({
    "customer_id": np.arange(1, N_CUST + 1),
    "gender": rng.choice(["Male", "Female"], N_CUST, p=[0.52, 0.48]),
    "age": np.clip(rng.normal(36, 11, N_CUST).round(), 18, 75).astype(int),
    "city": rng.choice(city_list, N_CUST, p=np.array([.25, .18, .10, .07, .08, .07, .05, .05, .08, .07])),
    "customer_segment": rng.choice(segments, N_CUST, p=seg_p),
})
seg_freq = {"Budget Shopper": 1.0, "Regular Family": 1.6, "Premium": 1.2, "Occasional": 0.4}
seg_basket = {"Budget Shopper": 0.85, "Regular Family": 1.25, "Premium": 1.15, "Occasional": 0.9}
seg_promo = {"Budget Shopper": 1.35, "Regular Family": 1.0, "Premium": 0.7, "Occasional": 1.0}
cust_w = dim_customer["customer_segment"].map(seg_freq).values * rng.gamma(2.0, 0.5, N_CUST)
cust_w = cust_w / cust_w.sum()

# ---------------------------------------------------------------- transactions
tx = pd.DataFrame({"transaction_id": np.arange(1, N_TX + 1)})
tx["date"] = rng.choice(dim_date["date"].values, N_TX, p=dim_date["day_weight"] / dim_date["day_weight"].sum())
tx["date"] = pd.to_datetime(tx["date"])

# store assignment: type weight x size factor x performance factor, new stores ramp up
type_w = {"Hypermarket": 3.2, "Supermarket": 1.6, "Express": 0.8, "Neighborhood": 0.55}
sw = (dim_store["store_type"].map(type_w)
      * (dim_store["store_size_sqft"] / dim_store.groupby("store_type")["store_size_sqft"].transform("mean")) ** 0.35
      * dim_store["_perf"])
sw = (sw / sw.sum()).values
assert abs(sw.sum() - 1) < 1e-9
tx["store_id"] = rng.choice(dim_store["store_id"].values, N_TX, p=sw)

# customers: same city bias (60% shop in a store of own city if one exists)
tx["customer_id"] = rng.choice(dim_customer["customer_id"].values, N_TX, p=cust_w)
tx = tx.merge(dim_customer[["customer_id", "customer_segment"]], on="customer_id", how="left")

# product assignment: weight = category demand x popularity, restricted by store assortment
cat_w = dim_product["category"].map({c: v[0] for c, v in categories.items()}).values
base_pw = cat_w / pd.Series(cat_w).groupby(dim_product["category"].values).transform("sum").values * 0 + 0  # placeholder
prod_w = (dim_product["category"].map({c: v[0] for c, v in categories.items()}).values
          * dim_product["_pop"].values
          / dim_product.groupby("category")["_pop"].transform("sum").values)
tx["product_id"] = 0
for sid, grp in tx.groupby("store_id"):
    mask = assortment[sid]
    w = prod_w * mask
    w = w / w.sum()
    tx.loc[grp.index, "product_id"] = rng.choice(dim_product["product_id"].values, len(grp), p=w)

tx = tx.merge(dim_product[["product_id", "category", "unit_cost", "selling_price"]], on="product_id", how="left")
tx = tx.merge(dim_store[["store_id", "store_type"]], on="store_id", how="left")

# promotions: store-type probability x segment sensitivity; WhiteFriday boosts promo prob
promo_p = {"Hypermarket": 0.25, "Supermarket": 0.30, "Express": 0.35, "Neighborhood": 0.40}
p = tx["store_type"].map(promo_p).values * tx["customer_segment"].map(seg_promo).values
ev = tx["date"].map(dim_date.set_index("date")["event"])
p = np.where(ev.isin(["White_Friday", "Eid_Fitr", "Ramadan"]).values, p * 1.25, p)
p = np.clip(p, 0, 0.85)
has_promo = rng.random(N_TX) < p
disc_levels = np.array([0.05, 0.10, 0.15, 0.20, 0.25])
# deeper discounts more likely in small-format stores and during White Friday
disc_probs_base = np.array([0.10, 0.20, 0.25, 0.30, 0.15])
disc = rng.choice(disc_levels, N_TX, p=disc_probs_base)
tx["discount_pct"] = np.where(has_promo, disc, 0.0)

# quantity: category-specific base demand x segment basket factor x PROMO ELASTICITY
# (units respond to discount depth; elasticity differs by category - staples respond most)
elasticity = {"Food & Beverages": 3.0, "Fresh Food": 2.5, "Household": 2.0, "Personal Care": 1.5,
              "Health & Wellness": 0.8, "Baby Care": 0.6, "Beauty": 2.0, "Electronics": 1.0}
qty_lambda = {"Food & Beverages": 2.2, "Fresh Food": 1.8, "Household": 1.5, "Personal Care": 1.4,
              "Health & Wellness": 1.2, "Baby Care": 1.6, "Beauty": 1.2, "Electronics": 0.25}
lam = (tx["category"].map(qty_lambda).values * tx["customer_segment"].map(seg_basket).values * QTY_SCALE
       * (1 + tx["category"].map(elasticity).values * tx["discount_pct"].values))
tx["quantity"] = 1 + rng.poisson(lam)
tx["unit_price"] = tx["selling_price"]

# financials (README formulas)
tx["gross_sales"] = (tx["quantity"] * tx["unit_price"]).round(2)
tx["discount_amount"] = (tx["gross_sales"] * tx["discount_pct"]).round(2)
tx["net_sales"] = (tx["gross_sales"] * (1 - tx["discount_pct"])).round(2)
tx["total_cost"] = (tx["quantity"] * tx["unit_cost"]).round(2)
tx["gross_profit"] = (tx["net_sales"] - tx["total_cost"]).round(2)

# payment and channel
tx["payment_method"] = rng.choice(["Mada", "Credit Card", "Cash", "Apple Pay", "STC Pay"], N_TX,
                                  p=[0.38, 0.22, 0.20, 0.12, 0.08])
chan_p = np.where(tx["store_type"].isin(["Express", "Neighborhood"]), 0.30, 0.12)  # delivery app share
tx["sales_channel"] = np.where(rng.random(N_TX) < chan_p, "Delivery App", "In-Store")
tx.rename(columns={"date": "transaction_date"}, inplace=True)

# ---------------------------------------------------------------- targets (need actuals to calibrate)
yearly = tx.assign(y=tx["transaction_date"].dt.year).groupby("store_id").agg(
    net=("net_sales", "sum"), gp=("gross_profit", "sum"))
yearly["margin"] = yearly["gp"] / yearly["net"]
# targets: annual sales target = actual avg annual x noise (some stores miss, some beat), margin target by type
noise = rng.normal(1.0, 0.12, len(yearly)).clip(0.75, 1.3)
tgt_margin_by_type = {"Hypermarket": 0.22, "Supermarket": 0.24, "Express": 0.27, "Neighborhood": 0.28}
dim_store["target_sales"] = (dim_store["store_id"].map(yearly["net"] / 3) * noise.round(3)[
    dim_store["store_id"].values - 1]).round(0)
dim_store["target_margin"] = dim_store["store_type"].map(tgt_margin_by_type)

# ---------------------------------------------------------------- export
final_tx_cols = ["transaction_id", "transaction_date", "store_id", "product_id", "customer_id", "quantity",
                 "unit_price", "gross_sales", "discount_amount", "discount_pct", "net_sales", "unit_cost",
                 "total_cost", "gross_profit", "payment_method", "sales_channel"]
tx = tx[final_tx_cols].sort_values("transaction_id")
tx["transaction_date"] = tx["transaction_date"].dt.date
dim_store.drop(columns="_perf").to_csv(OUT / "dim_store.csv", index=False)
dim_product.drop(columns="_pop").to_csv(OUT / "dim_product.csv", index=False)
dim_customer.to_csv(OUT / "dim_customer.csv", index=False)
dim_date.drop(columns="day_weight").to_csv(OUT / "dim_date.csv", index=False)
tx.to_csv(OUT / "fact_sales.csv", index=False)

print("fact_sales", tx.shape, "| stores", len(dim_store), "| products", len(dim_product), "| customers", len(dim_customer))
print("negative-profit tx:", int((tx.gross_profit < 0).sum()), f"({(tx.gross_profit < 0).mean():.2%})")
