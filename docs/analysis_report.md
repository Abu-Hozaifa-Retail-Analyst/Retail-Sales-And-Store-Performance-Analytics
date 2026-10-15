# GulfMart Retail Analytics: Findings and Recommendations

Scope: 25 stores, 500 SKUs, 5,000 customers, 120,000 transactions, Jan 2023 to Dec 2025. All amounts in SAR.
Data is synthetic. Patterns in it were partly built in by the generator (see "How far to trust these findings").

## 1. Executive summary

1. **Growth is slowing.** Net sales were SAR 6.53M in 2025, up 4.3%, after +7.6% in 2024. Gross margin is flat at 25.7%. Gross profit grew 5.1%.
2. **Discounting is the biggest controllable profit lever.** 31% of transactions carry a discount. Discounts cost SAR 1.14M over three years, equal to 24% of all gross profit. Units rise only 5% to 35% as discounts deepen, while gross margin falls from 29.9% (no discount) to 6.7% (25% off).
3. **Capping discounts at 10% adds about SAR 133k gross profit a year (+7.9%) with net sales essentially unchanged** (+0.2%). Capping at 15% adds SAR 66k (+3.9%).
4. **Electronics is the margin problem.** It is 9.0% of sales but 4.2% of profit (11.8% margin). It holds 1,074 of the 2,181 loss-making transactions and 86% of the loss value.
5. **Beauty is the profit engine.** 19.8% of sales, 29.3% of profit, 38.0% margin.
6. **Small formats chase volume with discounts.** Neighborhood stores discount at 8.0% of gross sales (Hypermarkets 4.9%) and earn the lowest margin (24.5%). Six stores sell above target but miss their margin target.
7. **Two stores need intervention:** Khobar EXP-21 and Dammam NEI-24 miss both sales and margin targets.
8. **Customers are concentrated.** Champions are 23% of customers and 50% of sales. 289 high-value customers (8% of sales) have gone quiet and are worth a win-back offer.

## 2. Data quality and validation
- 12 automated checks all pass: financial identities within 0.01 SAR, all foreign keys valid, quantity above zero, discounts within 0 to 25%, no future dates, no duplicate keys, no nulls.
- Negative-profit transactions are kept as a business finding, not treated as errors.
- 2.9% of transactions are high-value outliers (net sales above Q3 + 3 IQR). They are flagged, not removed, because they are legitimate large baskets (Beauty 52%, Electronics 20%, Baby Care 14%).

## 3. Sales performance
| Year | Net sales | Gross profit | GM % | Transactions | ATV | Sales growth |
|---|---|---|---|---|---|---|
| 2023 | 5.82M | 1.49M | 25.7% | 37,727 | 154 | n/a |
| 2024 | 6.26M | 1.60M | 25.5% | 40,137 | 156 | +7.6% |
| 2025 | 6.53M | 1.68M | 25.7% | 42,136 | 155 | +4.3% |

Growth comes from transaction count. ATV is flat at about SAR 155, so basket value is not improving.

**Seasonality.** Sales per day versus a normal day: White Friday +49%, Ramadan +36%, Eid al-Fitr +29%, Eid al-Adha +24%, National Day +18%. March is the strongest month (index 1.18), July and August the weakest (0.87). Friday and Saturday run 8% to 10% above the average day. Ramadan margin is 24.8% against 25.8% on normal days, with a higher discount rate (6.9% vs 5.6%), so peak events grow sales but give some margin back.

## 4. Store performance (2025)
- Action groups: 12 Star, 6 Volume without margin, 5 Profitable but under-selling, 2 Problem stores.
- **Volume without margin** (all Express or Neighborhood): Makkah EXP-18, Riyadh EXP-20, Jeddah EXP-17, Taif NEI-23, Abha EXP-22, Madinah NEI-25. Margin gaps run from -0.9 to -3.1 points, with discount rates of 6% to 9%.
- **Sales gap root cause.** Of the 9 stores below their peer median in sales per sqft, all are traffic-driven rather than basket-driven. Jeddah HYP-02 is the clearest case: 59% of the Hypermarket median, with transactions per sqft the main gap. Dammam HYP-04 sits at 77%.
- **Format economics.** Sales per sqft: Neighborhood 33.7, Express 23.9, Supermarket 8.7, Hypermarket 6.2. Bigger stores sell more in total but far less per sqft (rank correlation of size with productivity -0.91).
- **Clusters.** K-means on six productivity, basket and discount features gives four groups: large high-volume boxes, dense small formats with heavy discounting, mid-size supermarkets, and lower-ATV small stores.

## 5. Product and category
- Pareto: 101 SKUs (20%) deliver 70% of sales. 257 SKUs (51%) deliver only 10%.
- Demand versus margin matrix: 129 Stars, 121 Traffic drivers (high demand, low margin), 121 Niche (high margin), 129 Review/rationalise.
- 139 SKUs lose money at a 25% discount and 26 lose money at 20%, because their cost-to-price ratio leaves less than that much room. This is a product-by-product ceiling that a blanket promo calendar ignores.

## 6. Promotion and discount analysis
| Discount | Transactions | Units/tx | Gross margin | Loss-making |
|---|---|---|---|---|
| none | 82,338 | 3.68 | 29.9% | 0% |
| 5% | 3,765 | 3.86 | 26.0% | 0% |
| 10% | 7,503 | 4.14 | 22.0% | 0% |
| 15% | 9,476 | 4.44 | 17.7% | 2.1% |
| 20% | 11,308 | 4.70 | 12.7% | 5.0% |
| 25% | 5,610 | 4.97 | 6.7% | 25.2% |

- Within the same product, promo transactions carry about 20% more units than non-promo ones (paired t-test p < 0.001).
- Estimated category elasticity (units change per full point of discount): Food & Beverages 1.8, Fresh 1.5, Beauty 1.1, Household 1.1, Personal Care 0.9, Health 0.5, Baby Care 0.3, Electronics 0.25. **Electronics and Baby Care barely respond to discounts, so promoting them mostly gives margin away.**
- Promo ROI (incremental gross profit minus discount given away) is negative at every depth and worsens with depth: -4% at 5% off, -54% at 10%, -94% at 25%.
- Margin dilution on promo: Electronics -15.7 points, Food -14.5, Fresh -14.6, Baby Care -13.7, Beauty -11.7.

**Scenarios (2025, volumes adjusted by estimated elasticity):**
| Rule | Gross profit change | New GM % |
|---|---|---|
| Cap discounts at 20% | +SAR 18k (+1.1%) | 26.0% |
| Cap at 15% | +SAR 66k (+3.9%) | 26.7% |
| Cap at 10% | +SAR 133k (+7.9%) | 27.7% |
| No promo on Electronics | +SAR 28k (+1.6%) | 26.1% |
| Cap 15% and no Electronics promo | +SAR 88k (+5.2%) | 27.0% |
| Deep promos only in peak events, otherwise cap 10% | +SAR 110k (+6.6%) | 27.4% |

Net sales moves by less than 0.5% in every scenario.

## 7. Loss-making transactions
2,181 transactions (1.82%) lose money, SAR 18.1k in total. 91% happen at 20% or 25% discounts. The direct loss is small; the larger cost is margin dilution across all promoted sales. Cutting only the loss-makers (capping each SKU at its break-even tier) adds about SAR 28k, far less than a depth cap does.

## 8. Customers
- RFM segments: Champions 23% of customers and 50% of sales; Loyal 24% and 25%; At risk (high value) 6% and 8%; Lapsed 27% and 7%.
- Top 10% of customers give 32% of sales (Gini 0.48).
- Budget Shoppers use promos on 41% of transactions and earn 24.4% margin. Premium shoppers use promos on 22% and earn 26.7%. Regular Families are 54% of sales.
- Dammam, Riyadh and Madinah account for 51% of sales by customer city. Taif has the highest ATV (SAR 165).

## 9. Forecast
Holt-Winters projects 2026 net sales of SAR 6.67M (+2.2%). A 6-month holdout backtest gives 5.7% error, against 6.0% for a seasonal-naive benchmark, so the model beats the baseline only slightly. Treat the 80% band as indicative.

## 10. Recommendations (in priority order)
1. **Introduce a 10% to 15% promo depth ceiling** (largest lever, +4% to +8% gross profit). Pilot in 5 Supermarkets and 5 Express stores for 8 weeks, tracked against matched control stores.
2. **Stop promoting Electronics and Baby Care**, where customers barely react to discounts. Reprice or re-cost the 26 SKUs that lose money at 20%.
3. **Reserve deep discounts for Ramadan, Eid and White Friday**, when traffic is already high.
4. **Fix the two problem stores** (Khobar EXP-21, Dammam NEI-24) and set a margin gate on the six volume-without-margin stores.
5. **Investigate traffic at Jeddah HYP-02 and Dammam HYP-04**: location, local competition, weekday footfall, assortment.
6. **Grow basket value.** ATV has been flat for three years; test bundles and add-ons in Beauty and Personal Care.
7. **Run a win-back campaign for the 289 at-risk high-value customers** and a budget-shopper offer funded by the savings from item 1.
8. **Rationalise the C-class tail** (257 SKUs, 10% of sales), keeping any that anchor a basket.

## 11. How far to trust these findings
- **The data is simulated.** The generator built in category elasticities, higher discounts in small formats, a seasonal calendar and a cost-to-price structure. The pipeline recovers these patterns, which shows the method works, but the specific conclusions (for example "Electronics is unprofitable") describe the simulation, not a real retailer.
- **Store targets were set from actual sales plus random noise**, so "sales vs target" is illustrative and not an independent benchmark.
- **Customer retention is about 96% a year**, unrealistically high for grocery, so CLV is capped at 5 years (SAR 1,612 gross profit per customer).
- **Each transaction is a single product line**, so market basket analysis is not supported by this data model (under 0.1% of customer-store-days have two items). A real transaction-header and line-item model would enable it.
- **Scenario results assume estimated elasticities hold** and ignore competitor response, stock levels and traffic effects of promotions.
- This build is my own implementation of the README spec, because the repo's code and data folders were not readable. Its loss-making share (1.8%) and mean profit per transaction (SAR 39.8) are close to, but not identical to, the README's figures (2.36% and SAR 45.45).
