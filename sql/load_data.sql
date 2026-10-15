-- load_data.sql : set @path to the folder holding the CSVs (must be readable by the SQL Server service account)
USE GulfMartRetail; GO
DECLARE @path NVARCHAR(300) = N'C:\retail\data\raw\', @sql NVARCHAR(MAX);
DECLARE @t TABLE (tbl SYSNAME, file_name NVARCHAR(60));
INSERT @t VALUES ('dim_date','dim_date.csv'),('dim_store','dim_store.csv'),('dim_product','dim_product.csv'),
                 ('dim_customer','dim_customer.csv'),('fact_sales','fact_sales.csv');
-- dim_date.csv has extra column date order; load via staging if your column order differs (see docs/sql_notes.md)
DECLARE c CURSOR FOR SELECT tbl, file_name FROM @t;
DECLARE @tbl SYSNAME, @f NVARCHAR(60);
OPEN c; FETCH NEXT FROM c INTO @tbl, @f;
WHILE @@FETCH_STATUS = 0 BEGIN
  IF @tbl = 'dim_date'
     SET @sql = N'CREATE TABLE #d (d DATE,date_key INT,y INT,q INT,m INT,mn VARCHAR(12),w INT,dow VARCHAR(10),we BIT,ev VARCHAR(20),sm DECIMAL(6,3));
       BULK INSERT #d FROM ''' + @path + @f + ''' WITH (FIRSTROW=2, FIELDTERMINATOR='','', ROWTERMINATOR=''0x0a'', CODEPAGE=''65001'');
       INSERT dbo.dim_date SELECT date_key,d,y,q,m,mn,w,dow,we,ev,sm FROM #d;';
  ELSE
     SET @sql = N'BULK INSERT dbo.' + @tbl + N' FROM ''' + @path + @f + ''' WITH (FIRSTROW=2, FIELDTERMINATOR='','', ROWTERMINATOR=''0x0a'', CODEPAGE=''65001'', TABLOCK);';
  EXEC sp_executesql @sql;
  FETCH NEXT FROM c INTO @tbl, @f;
END
CLOSE c; DEALLOCATE c;
SELECT 'fact_sales' t, COUNT(*) n FROM dbo.fact_sales UNION ALL SELECT 'dim_store',COUNT(*) FROM dbo.dim_store
UNION ALL SELECT 'dim_product',COUNT(*) FROM dbo.dim_product UNION ALL SELECT 'dim_customer',COUNT(*) FROM dbo.dim_customer;
