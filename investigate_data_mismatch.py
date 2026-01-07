"""
Investigate data discrepancy between zrsd002.xlsx and fact_billing
Skills: data-analysis, debugging, databases
"""
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alkana_db")
engine = create_engine(DATABASE_URL)

print("="*80)
print("DATA INVESTIGATION: zrsd002.xlsx vs fact_billing")
print("="*80)

# 1. Read Excel file
print("\n1. Reading zrsd002.xlsx file...")
try:
    df = pd.read_excel("demodata/zrsd002.xlsx")
    print(f"   ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"   ✓ Columns: {list(df.columns[:10])}...")
    
    # Check date column
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'billing' in col.lower()]
    print(f"   ✓ Date-related columns: {date_cols}")
    
    # Find billing date column
    billing_date_col = None
    for col in df.columns:
        if 'billing' in col.lower() and 'date' in col.lower():
            billing_date_col = col
            break
    
    if billing_date_col:
        print(f"\n   Billing Date Column: '{billing_date_col}'")
        df[billing_date_col] = pd.to_datetime(df[billing_date_col], errors='coerce')
        print(f"   Date range: {df[billing_date_col].min()} to {df[billing_date_col].max()}")
        
        # Filter 2025 data
        df_2025 = df[(df[billing_date_col] >= '2025-01-01') & (df[billing_date_col] <= '2025-12-31')]
        print(f"\n   2025 Data: {len(df_2025)} rows")
        
        # Find net value column
        value_cols = [col for col in df.columns if 'value' in col.lower() or 'net' in col.lower()]
        print(f"   Value columns: {value_cols}")
        
        net_val_col = None
        for col in value_cols:
            if 'net' in col.lower() and 'value' in col.lower():
                net_val_col = col
                break
        
        if net_val_col:
            total_revenue_excel = df_2025[net_val_col].sum()
            print(f"\n   ✓ Total Revenue (2025) in Excel: {total_revenue_excel:,.2f}")
            print(f"   ✓ Total Orders (2025) in Excel: {df_2025['Billing Document'].nunique() if 'Billing Document' in df_2025.columns else 'N/A'}")
        
except Exception as e:
    print(f"   ✗ Error reading Excel: {e}")

# 2. Query database
print("\n2. Querying fact_billing table...")
try:
    with engine.connect() as conn:
        # Total revenue for 2025
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT billing_document) as total_orders,
                MIN(billing_date) as min_date,
                MAX(billing_date) as max_date,
                SUM(net_value) as total_revenue,
                COUNT(DISTINCT customer_name) as total_customers
            FROM fact_billing
            WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'
        """))
        row = result.fetchone()
        
        print(f"   ✓ Total Rows: {row[0]}")
        print(f"   ✓ Total Orders: {row[1]}")
        print(f"   ✓ Date Range: {row[2]} to {row[3]}")
        print(f"   ✓ Total Revenue: {row[4]:,.2f}")
        print(f"   ✓ Total Customers: {row[5]}")
        
        # Check raw data
        result2 = conn.execute(text("""
            SELECT COUNT(*) FROM raw_zrsd002
        """))
        raw_count = result2.fetchone()[0]
        print(f"\n   ✓ Raw zrsd002 rows: {raw_count}")
        
        # Check if data was transformed
        result3 = conn.execute(text("""
            SELECT 
                MIN(billing_date) as min_date,
                MAX(billing_date) as max_date,
                COUNT(*) as total_rows
            FROM fact_billing
        """))
        row3 = result3.fetchone()
        print(f"\n   All fact_billing data:")
        print(f"   Date range: {row3[0]} to {row3[1]}")
        print(f"   Total rows: {row3[2]}")
        
except Exception as e:
    print(f"   ✗ Error querying database: {e}")

# 3. Sample comparison
print("\n3. Sample Data Comparison...")
try:
    # Show first few rows from Excel
    print("\n   Excel Sample (first 3 rows):")
    print(df_2025[[billing_date_col, 'Billing Document', net_val_col]].head(3).to_string())
    
    # Show first few rows from database
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT billing_date, billing_document, net_value
            FROM fact_billing
            WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'
            ORDER BY billing_date
            LIMIT 3
        """))
        print("\n   Database Sample (first 3 rows):")
        for row in result:
            print(f"   {row[0]} | {row[1]} | {row[2]:,.2f}")
            
except Exception as e:
    print(f"   ✗ Error in comparison: {e}")

print("\n" + "="*80)
print("INVESTIGATION COMPLETE")
print("="*80)
