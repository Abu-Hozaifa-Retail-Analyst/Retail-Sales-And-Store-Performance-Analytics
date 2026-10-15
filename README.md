# GulfMart Retail Sales and Store Performance Analytics

End-to-end retail analytics project: synthetic Saudi/GCC retail data, Python analysis, SQL Server model and queries, DAX measures, a web dashboard, and a findings report.

## Run it
```
pip install -r requirements.txt
sh python/run_all.sh
```
Open `powerbi/gulfmart_dashboard.html`. For SQL Server, run `sql/create_tables.sql`, `load_data.sql` (edit the path), `constraints.sql`, `views/views.sql`, then `analysis/01_business_questions.sql`. The SQL has not been executed against a live SQL Server in this build; review the path and run on a dev database first.

## Contents
| Path | Purpose |
|---|---|
| `python/scripts/01_generate_data.py` | Star-schema generator (25 stores, 500 SKUs, 5,000 customers, 120k transactions) |
| `python/scripts/02_analysis.py` | Validation, KPIs, seasonality, store scorecard and root cause, clustering, ABC/XYZ, promo and elasticity, RFM, cohorts, forecast |
| `python/scripts/03_scenarios.py` | Discount-policy what-if models |
| `python/scripts/04_build_dashboard.py` | Builds the HTML dashboard |
| `sql/` | DDL, constraints, bulk load, views, business-question queries |
| `powerbi/dax_measures.dax` | Measure library for Power BI (model: fact_sales plus 4 dimensions) |
| `data/output/` | All analysis tables and `insights.json` |
| `docs/analysis_report.md` | Findings, recommendations, limitations |
| `docs/charts/` | Static charts |

## Headline results
Capping promo depth at 10% to 15% is worth +4% to +8% gross profit with net sales unchanged. Electronics earns 4% of profit on 9% of sales. Two stores miss both targets; six sell above target but miss margin.

All data is synthetic. See section 11 of the report for limitations.
