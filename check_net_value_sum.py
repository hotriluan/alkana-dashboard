"""Check sum of Net Value in zrsd002.xlsx vs database"""
import openpyxl
import pandas as pd
from src.db.connection import get_db
from sqlalchemy import text

# Read Excel file
print("=== Checking Excel file ===")
wb = openpyxl.load_workbook('demodata/zrsd002.XLSX')
ws = wb.active
headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
wb.close()

df = pd.read_excel('demodata/zrsd002.XLSX', header=None, skiprows=1, names=headers)
df = df.dropna(subset=['Billing Date'])
print(f"Total rows: {len(df)}")

# Find Net Value column
net_val_cols = [c for c in df.columns if c and 'net' in str(c).lower() and 'value' in str(c).lower()]
print(f"Net Value columns: {net_val_cols}")

if net_val_cols:
    col_name = net_val_cols[0]
    df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
    excel_total = df[col_name].sum()
    print(f"\n✓ Excel {col_name} sum: {excel_total:,.0f}")
    print(f"  User reported: 6,632,510,377")
    print(f"  Match: {abs(excel_total - 6632510377) < 1}")

# Check raw database
print("\n=== Checking Database ===")
db = next(get_db())

raw_total = db.execute(text("SELECT SUM(net_value) FROM raw_zrsd002")).scalar()
print(f"raw_zrsd002 net_value sum: {raw_total:,.0f}")

fact_total = db.execute(text("SELECT SUM(net_value) FROM fact_billing")).scalar()
print(f"fact_billing net_value sum: {fact_total:,.0f}")

# Check dashboard query
print("\n=== Executive Dashboard Query ===")
result = db.execute(text("""
    SELECT SUM(net_value) as total_revenue
    FROM fact_billing
    WHERE billing_date >= '2026-01-01' 
      AND billing_date <= '2026-01-08'
""")).scalar()
print(f"Dashboard range (01/01-08/01/2026): {result:,.0f}")

print("\n=== Analysis ===")
if excel_total and fact_total:
    diff = excel_total - fact_total
    print(f"Excel vs fact_billing difference: {diff:,.0f}")
    if abs(diff) > 1:
        print(f"⚠ MISMATCH! {diff:,.0f} missing from database")
    else:
        print("✓ Excel and database match")
