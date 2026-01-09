"""Debug why pandas reads headers as Unnamed"""
import pandas as pd
import openpyxl

# Method 1: Read with openpyxl directly
wb = openpyxl.load_workbook('demodata/zrsd002.XLSX')
ws = wb.active

print("=== openpyxl row 1 (index 0) ===")
first_row = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
print(f"First 10 cells: {first_row[:10]}")
print(f"Cell types: {[type(cell).__name__ for cell in first_row[:10]]}")

# Method 2: pandas read
print("\n=== pandas header=0 ===")
df = pd.read_excel('demodata/zrsd002.XLSX', header=0, dtype=str, nrows=2)
print(f"Columns: {list(df.columns)[:10]}")

# Method 3: pandas read without header, then check first row
print("\n=== pandas header=None ===")
df_raw = pd.read_excel('demodata/zrsd002.XLSX', header=None, dtype=str, nrows=2)
print(f"Row 0: {list(df_raw.iloc[0][:10])}")
print(f"Row 1: {list(df_raw.iloc[1][:10])}")
