"""Compare zrsd002.xlsx vs database for 2026-01-01 to 2026-01-08 only"""
import openpyxl
import pandas as pd
from src.db.connection import get_db
from sqlalchemy import text

# Read Excel file with corrected headers
print("=== Reading Excel file ===")
wb = openpyxl.load_workbook('demodata/zrsd002.XLSX')
ws = wb.active
headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
wb.close()

df = pd.read_excel('demodata/zrsd002.XLSX', header=None, skiprows=1, names=headers)
df = df.dropna(subset=['Billing Date'])
df['Billing Date'] = pd.to_datetime(df['Billing Date'])

# Filter for 2026-01-01 to 2026-01-08
df_2026 = df[(df['Billing Date'] >= '2026-01-01') & (df['Billing Date'] <= '2026-01-08')]
df_2026['Net Value'] = pd.to_numeric(df_2026['Net Value'], errors='coerce')

excel_count = len(df_2026)
excel_sum = df_2026['Net Value'].sum()

print(f"Excel (2026-01-01 to 2026-01-08):")
print(f"  Records: {excel_count}")
print(f"  Net Value sum: {excel_sum:,.0f}")
print(f"\nDate distribution:")
print(df_2026['Billing Date'].value_counts().sort_index())

# Check database
print("\n=== Checking Database ===")
db = next(get_db())

db_result = db.execute(text("""
    SELECT COUNT(*), SUM(net_value)
    FROM raw_zrsd002
    WHERE billing_date >= '2026-01-01' 
      AND billing_date <= '2026-01-08'
""")).fetchone()

db_count = db_result[0]
db_sum = db_result[1] if db_result[1] else 0

print(f"raw_zrsd002 (2026-01-01 to 2026-01-08):")
print(f"  Records: {db_count}")
print(f"  Net Value sum: {db_sum:,.0f}")

print("\n=== Comparison ===")
print(f"Records: Excel={excel_count}, DB={db_count}, Diff={excel_count - db_count}")
print(f"Net Value: Excel={excel_sum:,.0f}, DB={db_sum:,.0f}, Diff={excel_sum - db_sum:,.0f}")

if excel_count != db_count:
    print(f"\n⚠ MISSING {excel_count - db_count} records in database!")
    print("Need to reload zrsd002.xlsx with fixed loader")
else:
    print("\n✓ Record count matches")
    
if abs(excel_sum - db_sum) > 100:
    print(f"⚠ Net Value mismatch: {excel_sum - db_sum:,.0f}")
else:
    print("✓ Net Value matches")
