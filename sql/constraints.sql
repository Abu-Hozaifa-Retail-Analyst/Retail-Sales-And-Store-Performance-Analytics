-- constraints.sql : referential integrity, business-rule checks, indexes
USE GulfMartRetail; GO
ALTER TABLE dbo.fact_sales ADD
  CONSTRAINT fk_fs_store    FOREIGN KEY (store_id)    REFERENCES dbo.dim_store(store_id),
  CONSTRAINT fk_fs_product  FOREIGN KEY (product_id)  REFERENCES dbo.dim_product(product_id),
  CONSTRAINT fk_fs_customer FOREIGN KEY (customer_id) REFERENCES dbo.dim_customer(customer_id),
  CONSTRAINT fk_fs_date     FOREIGN KEY (transaction_date) REFERENCES dbo.dim_date([date]),
  CONSTRAINT ck_fs_qty      CHECK (quantity > 0),
  CONSTRAINT ck_fs_disc     CHECK (discount_pct BETWEEN 0 AND 0.25),
  CONSTRAINT ck_fs_net      CHECK (ABS(net_sales - gross_sales * (1 - discount_pct)) <= 0.011),
  CONSTRAINT ck_fs_gp       CHECK (ABS(gross_profit - (net_sales - total_cost)) <= 0.011);
-- NOTE: negative gross_profit is deliberately allowed (promo-driven losses are a business finding, not an error)
CREATE INDEX ix_fs_date_store ON dbo.fact_sales(transaction_date, store_id) INCLUDE (net_sales, gross_profit, quantity);
CREATE INDEX ix_fs_product    ON dbo.fact_sales(product_id) INCLUDE (net_sales, gross_profit, quantity, discount_pct);
CREATE INDEX ix_fs_customer   ON dbo.fact_sales(customer_id) INCLUDE (net_sales, gross_profit, transaction_date);
GO
