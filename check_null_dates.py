"""Check which rows have NULL billing dates in Excel"""
import openpyxl
import pandas as pd

wb = openpyxl.load_workbook('demodata/zrsd002.XLSX')
ws = wb.active
headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
wb.close()

df = pd.read_excel('demodata/zrsd002.XLSX', header=None, skiprows=1, names=headers)

print(f"Total rows: {len(df)}")
null_dates = df[df['Billing Date'].isna()]
print(f"Rows with NULL Billing Date: {len(null_dates)}")

if len(null_dates) > 0:
    print("\nSample rows with NULL dates:")
    print(null_dates.head(10)[['Billing Date', 'Billing Document', 'Net Value']])
    
    # Check if these have Net Value
    null_dates['Net Value'] = pd.to_numeric(null_dates['Net Value'], errors='coerce')
    total_null_net = null_dates['Net Value'].sum()
    print(f"\n✓ Net Value in NULL-date rows: {total_null_net:,.0f}")
    
# Check rows WITH dates
valid_dates = df[df['Billing Date'].notna()]
print(f"\nRows with valid Billing Date: {len(valid_dates)}")
valid_dates['Net Value'] = pd.to_numeric(valid_dates['Net Value'], errors='coerce')
total_valid_net = valid_dates['Net Value'].sum()
print(f"Net Value in valid-date rows: {total_valid_net:,.0f}")

print(f"\nTotal Net Value: {total_null_net + total_valid_net:,.0f}")
print(f"User reported: 6,632,510,377")
