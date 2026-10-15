-- views.sql : semantic layer for Power BI and ad-hoc analysis
USE GulfMartRetail; GO
CREATE OR ALTER VIEW dbo.vw_sales_enriched AS
SELECT f.*, YEAR(f.transaction_date) AS yr, DATEFROMPARTS(YEAR(f.transaction_date),MONTH(f.transaction_date),1) AS month_start,
       s.store_name, s.city AS store_city, s.region, s.store_type, s.store_size_sqft,
       p.category, p.subcategory, p.brand, c.customer_segment, d.[event], d.is_weekend,
       CASE WHEN f.discount_pct > 0 THEN 1 ELSE 0 END AS is_promo,
       CASE WHEN f.gross_profit < 0 THEN 1 ELSE 0 END AS is_loss_tx
FROM dbo.fact_sales f
JOIN dbo.dim_store s ON s.store_id=f.store_id JOIN dbo.dim_product p ON p.product_id=f.product_id
JOIN dbo.dim_customer c ON c.customer_id=f.customer_id JOIN dbo.dim_date d ON d.[date]=f.transaction_date;
GO
CREATE OR ALTER VIEW dbo.vw_store_year_kpi AS
SELECT store_id, store_name, store_type, city = store_city, yr,
       SUM(net_sales) net_sales, SUM(gross_profit) gross_profit, SUM(gross_profit)/NULLIF(SUM(net_sales),0) gm_pct,
       COUNT(*) transactions, SUM(quantity) units, SUM(net_sales)/COUNT(*) atv, 1.0*SUM(quantity)/COUNT(*) upt,
       SUM(discount_amount)/NULLIF(SUM(gross_sales),0) discount_rate, AVG(1.0*is_promo) promo_penetration, AVG(1.0*is_loss_tx) loss_tx_pct
FROM dbo.vw_sales_enriched GROUP BY store_id, store_name, store_type, store_city, yr;
GO
CREATE OR ALTER VIEW dbo.vw_store_scorecard_2025 AS
WITH k AS (SELECT k.*, s.store_size_sqft, s.target_sales, s.target_margin FROM dbo.vw_store_year_kpi k JOIN dbo.dim_store s ON s.store_id=k.store_id WHERE yr=2025)
SELECT *, net_sales/target_sales-1 AS sales_vs_target, (gm_pct-target_margin)*100 AS margin_vs_target_pp,
       net_sales/store_size_sqft AS sales_per_sqft,
       CASE WHEN net_sales>=target_sales AND gm_pct>=target_margin THEN 'Star'
            WHEN net_sales>=target_sales THEN 'Volume without margin'
            WHEN gm_pct>=target_margin THEN 'Profitable but under-selling' ELSE 'Problem store' END AS quadrant
FROM k;
GO
CREATE OR ALTER VIEW dbo.vw_product_abc AS
WITH p AS (SELECT product_id, SUM(net_sales) net_sales, SUM(gross_profit) gp FROM dbo.fact_sales GROUP BY product_id),
c AS (SELECT *, SUM(net_sales) OVER (ORDER BY net_sales DESC ROWS UNBOUNDED PRECEDING)*1.0/SUM(net_sales) OVER () cum_share FROM p)
SELECT c.*, pr.product_name, pr.category, pr.unit_cost, pr.selling_price, 1-pr.unit_cost/pr.selling_price AS breakeven_discount,
       CASE WHEN cum_share<=.70 THEN 'A' WHEN cum_share<=.90 THEN 'B' ELSE 'C' END AS abc_class
FROM c JOIN dbo.dim_product pr ON pr.product_id=c.product_id;
GO
CREATE OR ALTER VIEW dbo.vw_customer_rfm AS
WITH b AS (SELECT customer_id, DATEDIFF(DAY, MAX(transaction_date), '2026-01-01') recency, COUNT(*) frequency, SUM(net_sales) monetary, SUM(gross_profit) gp
           FROM dbo.fact_sales GROUP BY customer_id),
s AS (SELECT *, NTILE(5) OVER (ORDER BY recency DESC) R, NTILE(5) OVER (ORDER BY frequency) F, NTILE(5) OVER (ORDER BY monetary) M FROM b)
SELECT *, CASE WHEN R>=4 AND F>=4 AND M>=4 THEN 'Champions' WHEN R>=3 AND F>=3 THEN 'Loyal'
              WHEN R>=4 AND F<=2 THEN 'New / Promising' WHEN R<=2 AND F>=4 THEN 'At risk (high value)'
              WHEN R<=2 AND F<=2 THEN 'Lapsed' ELSE 'Needs attention' END AS rfm_segment FROM s;
GO
