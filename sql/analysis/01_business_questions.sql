-- 01_business_questions.sql : answers to the README business questions (T-SQL)
USE GulfMartRetail; GO
-- Q1 Executive KPIs by year with YoY
WITH y AS (SELECT yr, SUM(net_sales) ns, SUM(gross_profit) gp, COUNT(*) tx, SUM(quantity) u, SUM(discount_amount)/SUM(gross_sales) dr FROM dbo.vw_sales_enriched GROUP BY yr)
SELECT yr, ns, gp, gp/ns gm_pct, tx, ns/tx atv, 1.0*u/tx upt, dr, ns/LAG(ns) OVER (ORDER BY yr)-1 sales_yoy, gp/LAG(gp) OVER (ORDER BY yr)-1 gp_yoy FROM y;

-- Q2 Store productivity vs peer median of same store type (2025)
SELECT s.store_name, s.store_type, s.sales_per_sqft,
       s.sales_per_sqft / m.med AS peer_index, s.quadrant
FROM dbo.vw_store_scorecard_2025 s
JOIN (SELECT DISTINCT store_type, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sales_per_sqft) OVER (PARTITION BY store_type) med FROM dbo.vw_store_scorecard_2025) m
  ON m.store_type = s.store_type ORDER BY peer_index;

-- Q3 Category contribution: sales share vs profit share
SELECT category, SUM(net_sales) ns, SUM(gross_profit) gp, SUM(gross_profit)/SUM(net_sales) gm_pct,
       SUM(net_sales)/SUM(SUM(net_sales)) OVER () sales_share, SUM(gross_profit)/SUM(SUM(gross_profit)) OVER () profit_share
FROM dbo.fact_sales f JOIN dbo.dim_product p ON p.product_id=f.product_id GROUP BY category ORDER BY gp DESC;

-- Q4 Discount ladder: margin, units, loss rate by discount depth
SELECT discount_pct, COUNT(*) tx, AVG(1.0*quantity) avg_units, SUM(gross_profit)/SUM(net_sales) gm_pct,
       AVG(CASE WHEN gross_profit<0 THEN 1.0 ELSE 0 END) loss_rate, SUM(discount_amount) discount_cost
FROM dbo.fact_sales GROUP BY discount_pct ORDER BY discount_pct;

-- Q5 Products that become loss-making after discount (break-even test)
SELECT TOP 25 p.product_name, p.category, 1-p.unit_cost/p.selling_price AS breakeven_discount,
       COUNT(*) loss_tx, SUM(f.gross_profit) total_loss
FROM dbo.fact_sales f JOIN dbo.dim_product p ON p.product_id=f.product_id WHERE f.gross_profit<0
GROUP BY p.product_name, p.category, p.unit_cost, p.selling_price ORDER BY total_loss;

-- Q6 Event uplift vs a normal day
WITH d AS (SELECT [event], COUNT(DISTINCT transaction_date) days, SUM(net_sales) ns, SUM(gross_profit) gp, SUM(discount_amount)/SUM(gross_sales) dr FROM dbo.vw_sales_enriched GROUP BY [event])
SELECT [event], days, ns/days sales_per_day, ns/days / (SELECT ns/days FROM d WHERE [event]='No Event') - 1 uplift, gp/ns gm_pct, dr FROM d ORDER BY uplift DESC;

-- Q7 Store-type promo behaviour
SELECT store_type, AVG(1.0*is_promo) promo_pen, SUM(discount_amount)/SUM(gross_sales) disc_rate, SUM(gross_profit)/SUM(net_sales) gm_pct
FROM dbo.vw_sales_enriched GROUP BY store_type;

-- Q8 RFM segment value
SELECT rfm_segment, COUNT(*) customers, SUM(monetary) net_sales, SUM(monetary)/SUM(SUM(monetary)) OVER () sales_share, AVG(1.0*frequency) avg_freq
FROM dbo.vw_customer_rfm GROUP BY rfm_segment ORDER BY net_sales DESC;

-- Q9 Month-over-month and rolling 3-month sales
WITH m AS (SELECT month_start, SUM(net_sales) ns FROM dbo.vw_sales_enriched GROUP BY month_start)
SELECT month_start, ns, ns/LAG(ns) OVER (ORDER BY month_start)-1 mom, AVG(ns) OVER (ORDER BY month_start ROWS 2 PRECEDING) ma3,
       ns/LAG(ns,12) OVER (ORDER BY month_start)-1 yoy FROM m;
