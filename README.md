# Retail Sales & Store Performance Analytics

## 📊 Project Overview

This project is an end-to-end **Retail Sales & Store Performance Analytics** project designed to simulate a realistic Saudi/GCC retail business environment.

The project focuses on transforming raw retail transaction data into actionable business insights using:

- Python
- Pandas
- NumPy
- SQL Server
- Power BI
- DAX
- Git & GitHub

The objective is not only to calculate sales KPIs, but to demonstrate **retail business thinking** — understanding sales performance, customer behavior, product demand, promotions, profitability, store differences, and potential business actions.

---

# 🎯 Business Objective

The primary business objective is to answer questions such as:

- Which stores generate the highest sales?
- Which store types perform best?
- How do store size and store format affect transaction volume?
- Which products and categories drive demand?
- How do promotions affect sales and profitability?
- Which transactions become loss-making after discounts?
- Which stores or products require management attention?
- How can management improve sales and profitability?

The project follows a business analytics workflow:

```text
Raw Data
   ↓
Data Profiling
   ↓
Data Cleaning
   ↓
Data Validation
   ↓
Transaction Generation
   ↓
KPI Calculation
   ↓
Store Performance Analysis
   ↓
Product & Customer Analysis
   ↓
Promotion Analysis
   ↓
Root Cause Analysis
   ↓
Power BI Dashboard
   ↓
Business Recommendations






🏪 Retail Business Scenario

The fictional company used in this project is GulfMart, a Saudi/GCC-style retail business.

The dataset represents a multi-store retail operation containing:

Hypermarkets
Supermarkets
Express stores
Neighborhood stores

The dataset is synthetic and was designed specifically for analytics practice and portfolio development.

📦 Dataset Design

The project is designed around a retail star-schema structure.

Main Tables
fact_sales
dim_store
dim_product
dim_customer
dim_date
Dataset Scale
Entity	Volume
Stores	25
Products	500
Customers	5,000
Sales Transactions	120,000
Historical Period	Multi-year
⭐ Data Model

The project uses a Star Schema.

                    dim_date
                       |
                       |
dim_customer ---- fact_sales ---- dim_product
                       |
                       |
                   dim_store
Fact Table
fact_sales

Contains transaction-level retail sales information.

Key fields include:

transaction_id
transaction_date
store_id
product_id
customer_id
quantity
unit_price
gross_sales
discount_amount
discount_pct
net_sales
unit_cost
total_cost
gross_profit
payment_method
sales_channel
🏬 Store Dimension
dim_store

Contains store-level attributes.

Key fields include:

store_id
store_name
city
region
store_type
store_size_sqft
opening_date
target_sales
target_margin
Store Types

The current store network contains:

Store Type	Stores
Supermarket	10
Express	7
Hypermarket	5
Neighborhood	3
Total	25
🛒 Product Dimension
dim_product

Contains product master information.

Key fields include:

product_id
product_name
category
subcategory
brand
unit_cost
selling_price
Product Categories

The current product taxonomy contains:

Food & Beverages
Fresh Food
Health & Wellness
Personal Care
Beauty
Household
Baby Care
Electronics

Category-level demand weights are used during synthetic transaction generation to create realistic differences in product demand.

👥 Customer Dimension
dim_customer

Contains customer-level information.

Key fields include:

customer_id
gender
age
city
customer_segment

Customers are used to simulate differences in purchasing frequency and geographic behavior.

📅 Date Dimension
dim_date

Contains calendar attributes used for time-based retail analysis.

Fields include:

date
year
quarter
month
month_name
week
day_of_week

The date dimension supports future analysis of:

Monthly sales
Year-over-year performance
Seasonality
Weekday vs weekend behavior
Quarterly trends
🐍 Python Transaction Generation

Python is being used to create a realistic synthetic retail transaction dataset.

The transaction-generation process includes:

Transaction Skeleton
        ↓
Transaction Dates
        ↓
Store Assignment
        ↓
Customer Assignment
        ↓
Product Assignment
        ↓
Quantity Generation
        ↓
Pricing
        ↓
Promotions
        ↓
Cost Calculation
        ↓
Gross Profit
        ↓
Validation

The project uses:

Pandas
NumPy
Vectorized operations
Probability-based sampling
Business-rule-based synthetic data generation
🏬 Store Assignment Logic

Transactions are distributed across stores using a probability-based approach.

Store transaction probability considers:

Store type
Store size
Store performance factor

The current store types are:

Hypermarket
Supermarket
Express
Neighborhood

Larger stores and higher-performing store formats receive higher transaction weights.

This allows the dataset to contain realistic differences in transaction volume between stores.

🛍️ Store Product Assortment

Product availability differs by store type.

Synthetic assortment probabilities are currently modeled as:

Store Type	Assortment Probability
Hypermarket	90%
Supermarket	75%
Express	45%
Neighborhood	35%

This reflects the assumption that larger-format stores carry broader product assortments.

These values are synthetic modeling assumptions and are not intended to represent actual GulfMart policies.

🎯 Promotion Behavior

Promotion probability also varies by store type.

Current synthetic promotion probabilities:

Store Type	Promotion Probability
Hypermarket	25%
Supermarket	30%
Express	35%
Neighborhood	40%

This creates variation in promotional behavior between store formats.

The objective is to later analyze:

Promotion
    ↓
Discount
    ↓
Net Sales
    ↓
Gross Profit
    ↓
Margin Impact
💰 Financial Calculations

The transaction model calculates the following financial metrics.

Gross Sales
Gross Sales = Quantity × Unit Price
Net Sales
Net Sales = Gross Sales × (1 − Discount %)
Total Cost
Total Cost = Quantity × Unit Cost
Gross Profit
Gross Profit = Net Sales − Total Cost

These calculations have been validated using a 0.01 currency-unit tolerance to account for monetary rounding and floating-point precision.

🔍 Financial Validation

The following validation checks have passed:

PASS: Gross sales calculation
PASS: Net sales calculation
PASS: Total cost calculation
PASS: Gross profit calculation

The financial calculation validation was completed successfully across the generated transaction dataset.

⚠️ Loss-Making Transactions

The dataset intentionally allows some promotional transactions to become loss-making.

Current validation:

Total transactions:          120,000
Negative-profit transactions: 2,832
Negative-profit percentage:     2.36%

This behavior was retained intentionally.

The negative-profit transactions are not treated as data-quality errors.

They represent a potential retail business scenario:

High Discount
      ↓
Lower Net Sales
      ↓
Margin Erosion
      ↓
Negative Gross Profit

This will provide an opportunity for future analysis of promotional effectiveness and margin risk.

📊 Gross Profit Validation

Current gross-profit summary:

Metric	Value
Transactions	120,000
Mean Gross Profit	45.45
Median Gross Profit	36.84
Minimum Gross Profit	-224.18
25th Percentile	18.82
75th Percentile	59.53
Maximum Gross Profit	539.44

The majority of transactions are profitable, while a smaller percentage become loss-making.

🔎 Promotion & Profitability Analysis

Negative-profit transactions were analyzed by discount level.

Discount	Loss-Making Transactions	Total Loss
5%	1	-0.52
10%	42	-296.22
15%	445	-3,077.48
20%	1,338	-11,912.13
25%	1,006	-11,316.72

This demonstrates a clear analytical opportunity:

Higher promotional discounts can increase the risk of margin erosion when product cost is relatively high.

This will later be investigated by:

Store
Product
Category
Promotion level
Store type
Customer segment
🧪 Data Validation Approach

The project uses validation checks throughout the data-generation process.

Examples include:

Store Validation
Missing store IDs = 0
Unique stores assigned = 25
Store probability total = 1.0
Product Validation

Product-category mappings are checked to ensure every product category has a valid demand weight.

Financial Validation

The following relationships are validated:

Gross Sales
Net Sales
Total Cost
Gross Profit

Financial validations use a small currency tolerance instead of requiring exact floating-point equality.

🧠 Business Questions

The completed dataset will eventually be used to answer:

Sales Performance
What are total sales?
What are sales trends over time?
Which stores generate the highest sales?
Which stores are underperforming?
Store Performance
Which store type performs best?
Does store size correlate with sales?
Which stores have high transaction volume but weak profitability?
Which stores exceed their targets?
Product Performance
Which products generate the most sales?
Which categories generate the most profit?
Which products have high demand but low margins?
Promotion Analysis
Which discounts drive sales?
Which discounts reduce profitability?
Which stores have the highest promotional activity?
Which products become loss-making after discounts?
Customer Analysis
Which customer segments generate the most revenue?
Which customers purchase most frequently?
Which cities generate the highest sales?
📈 Planned KPIs

The project will calculate retail KPIs including:

Sales KPIs
Net Sales
Gross Sales
Transactions
Units Sold
Average Transaction Value (ATV)
Units Per Transaction (UPT)
Profitability KPIs
Gross Profit
Gross Margin %
Profit per Transaction
Discount Rate
Store KPIs
Sales per Store
Transactions per Store
Sales vs Target
Margin vs Target
Store Productivity
Customer KPIs
Active Customers
Customer Sales
Average Customer Value
Purchase Frequency
Product KPIs
Product Sales
Product Profit
Product Margin
Units Sold
Category Contribution
📊 Power BI Dashboard

Power BI will be used to build an executive retail performance dashboard.

Planned dashboard areas include:

Page 1 — Executive Retail Overview

KPIs:

Net Sales
Gross Profit
Gross Margin %
Transactions
Units Sold
ATV
UPT

Visuals:

Sales trend
Sales by store
Sales by store type
Sales by category
Profitability overview
Page 2 — Store Performance

Analysis of:

Store sales
Store targets
Store profitability
Store type
Store size
Transaction volume
Future Pages
Product Performance
Customer Analytics
Promotion & Discount Analysis
Profitability Analysis
Executive Recommendations
🛠️ Technology Stack
Tool	Purpose
Python	Data generation and analysis
Pandas	Data manipulation
NumPy	Numerical calculations and simulation
SQL Server	Data storage and SQL analytics
SSMS	Database development
Power BI	Dashboard and visualization
DAX	KPI calculations
Git	Version control
GitHub	Portfolio and project management
VS Code	Development environment
📁 Project Structure

The project is being organized approximately as follows:

Retail-Sales-Store-Performance/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── output/
│
├── python/
│   ├── notebooks/
│   └── scripts/
│
├── sql/
│   ├── create_tables.sql
│   ├── constraints.sql
│   ├── load_data.sql
│   ├── analysis/
│   └── views/
│
├── powerbi/
│   └── retail_sales_store_performance.pbix
│
├── docs/
│
├── README.md
├── .gitignore
└── pyproject.toml

The exact structure may evolve as the project progresses.

🔄 Project Workflow

The complete project is being developed incrementally.

Phase 1 — Business & Data Design
Define retail business scenario
Define data model
Define dimensions
Define fact table
Define KPIs
Phase 2 — Synthetic Data Generation
Generate stores
Generate products
Generate customers
Generate dates
Generate transactions
Add realistic business behavior
Phase 3 — Data Quality
Profile data
Identify missing values
Identify duplicates
Validate data types
Validate relationships
Validate financial calculations
Phase 4 — SQL Analytics
Load data into SQL Server
Build analytical queries
Create views
Calculate KPIs
Perform store and product analysis
Phase 5 — Power BI
Build data model
Create DAX measures
Create dashboard pages
Add slicers
Add conditional formatting
Create executive visuals
Phase 6 — Business Analysis
Identify performance gaps
Diagnose root causes
Analyze promotions
Analyze profitability
Develop recommendations
Phase 7 — Portfolio & Interview Preparation
Document project
Push project to GitHub
Create project summary
Create LinkedIn portfolio content
Prepare interview questions
Practice explaining business insights
🚀 Current Project Status
Completed
 Retail business scenario defined
 Star schema designed
 Store dimension created
 Product dimension created
 Customer dimension created
 Date dimension created
 Transaction generation framework created
 120,000 transactions generated
 Store assignment completed
 Store-type assortment logic completed
 Product category demand logic implemented
 Promotion behavior implemented
 Pricing logic implemented
 Cost logic implemented
 Gross profit logic implemented
 Negative-profit behavior investigated
 Financial calculation validation completed
Current Status

🚧 Synthetic transaction generation and validation are still in progress.

Next steps include:

Complete store-type promotion validation
Complete product assignment validation
Validate customer/product/store relationships
Finalize transaction dataset
Export CSV files
Load data into SQL Server
Build SQL analytics
Build Power BI dashboard
💡 Key Learning Outcomes

This project is designed to demonstrate more than technical skills.

It demonstrates the ability to:

Think like a retail analyst
Translate business questions into data problems
Build realistic retail datasets
Validate data systematically
Use Python for data preparation
Use SQL for business analysis
Build Power BI dashboards
Calculate and interpret retail KPIs
Investigate profitability
Analyze promotional impact
Identify root causes
Translate analysis into business recommendations
👔 Portfolio Objective

This project is intended as a portfolio project for roles such as:

Retail Analyst
Retail Data Analyst
Business Data Analyst
BI Analyst
Sales Analyst
Commercial Analyst
E-commerce Analyst

The project is specifically designed around retail use cases relevant to the Saudi/GCC retail and e-commerce environment.

📌 Important Note

This is a synthetic retail analytics project.

The company, stores, products, customers, transactions, targets, probabilities, and business assumptions are simulated for educational and portfolio purposes.

The purpose is to demonstrate:

Technical Skills
        +
Retail Business Knowledge
        +
Data Analytics
        +
Business Storytelling

rather than represent actual company performance.

📈 Future Enhancements

Potential future enhancements include:

Sales forecasting
Customer RFM segmentation
Market basket analysis
Price elasticity analysis
Promotion effectiveness
Store clustering
Product ABC analysis
Inventory optimization
Stockout analysis
Customer lifetime value
Advanced Power BI executive dashboard
Automated ETL pipeline
SQL stored procedures
Data quality monitoring
Automated KPI reporting
👤 Author

Retail Analytics Portfolio Project

Focus areas:

Retail Analytics
Data Analytics
Business Intelligence
SQL
Python
Power BI
Customer Analytics
Store Performance
Sales Analytics
```
