"""Check exact Excel structure of zrsd002.XLSX"""
import openpyxl

wb = openpyxl.load_workbook('demodata/zrsd002.XLSX')
ws = wb.active

print("First 5 rows:")
for i, row in enumerate(ws.iter_rows(max_row=5, values_only=True)):
    print(f"Row {i}: {row[:8]}")
