"""Inspect zrsd004.XLSX file structure to find headers"""
import openpyxl
import pandas as pd

file_path = 'demodata/zrsd004.XLSX'

print("=" * 80)
print("Using openpyxl to inspect raw Excel rows:")
print("=" * 80)
wb = openpyxl.load_workbook(file_path)
ws = wb.active

for i in range(1, 6):
    row_vals = [cell.value for cell in ws[i]]
    print(f"\nRow {i}:")
    print(row_vals[:12])  # First 12 columns

print("\n" + "=" * 80)
print("Using pandas with different header settings:")
print("=" * 80)

print("\n1. With header=0 (default - first row as header):")
df = pd.read_excel(file_path, header=0)
print(f"Columns: {df.columns.tolist()[:10]}")
print(f"First data row: {df.iloc[0].tolist()[:5]}")

print("\n2. With header=None (no header, all data):")
df = pd.read_excel(file_path, header=None, nrows=3)
print(df)

print("\n3. With header=1 (second row as header):")
df = pd.read_excel(file_path, header=1, nrows=2)
print(f"Columns: {df.columns.tolist()[:10]}")
