-- create_tables.sql  |  SQL Server 2019+  |  GulfMart star schema
IF DB_ID('GulfMartRetail') IS NULL CREATE DATABASE GulfMartRetail;
GO
USE GulfMartRetail;
GO
DROP TABLE IF EXISTS dbo.fact_sales, dbo.dim_store, dbo.dim_product, dbo.dim_customer, dbo.dim_date;
GO
CREATE TABLE dbo.dim_date (
    date_key INT NOT NULL PRIMARY KEY, [date] DATE NOT NULL UNIQUE,
    [year] SMALLINT, [quarter] TINYINT, [month] TINYINT, month_name VARCHAR(12), [week] TINYINT,
    day_of_week VARCHAR(10), is_weekend BIT, [event] VARCHAR(20), season_mult DECIMAL(6,3));
CREATE TABLE dbo.dim_store (
    store_id INT NOT NULL PRIMARY KEY, store_name VARCHAR(60) NOT NULL, city VARCHAR(30), region VARCHAR(20),
    store_type VARCHAR(20) NOT NULL, store_size_sqft INT, opening_date DATE, target_sales DECIMAL(14,2), target_margin DECIMAL(5,4));
CREATE TABLE dbo.dim_product (
    product_id INT NOT NULL PRIMARY KEY, product_name VARCHAR(60), category VARCHAR(30) NOT NULL, subcategory VARCHAR(30),
    brand VARCHAR(20), unit_cost DECIMAL(10,2), selling_price DECIMAL(10,2));
CREATE TABLE dbo.dim_customer (
    customer_id INT NOT NULL PRIMARY KEY, gender VARCHAR(8), age TINYINT, city VARCHAR(30), customer_segment VARCHAR(20));
CREATE TABLE dbo.fact_sales (
    transaction_id INT NOT NULL PRIMARY KEY, transaction_date DATE NOT NULL,
    store_id INT NOT NULL, product_id INT NOT NULL, customer_id INT NOT NULL, quantity INT NOT NULL,
    unit_price DECIMAL(10,2), gross_sales DECIMAL(12,2), discount_amount DECIMAL(12,2), discount_pct DECIMAL(4,2),
    net_sales DECIMAL(12,2), unit_cost DECIMAL(10,2), total_cost DECIMAL(12,2), gross_profit DECIMAL(12,2),
    payment_method VARCHAR(15), sales_channel VARCHAR(15));
GO
