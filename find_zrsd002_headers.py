"""Find where real headers are in zrsd002.XLSX"""
import openpyxl

wb = openpyxl.load_workbook('demodata/zrsd002.XLSX')
ws = wb.active

print("First 10 rows to identify header location:")
for i, row in enumerate(ws.iter_rows(max_row=10, values_only=True)):
    # Show first 5 columns
    row_preview = row[:5]
    print(f"Row {i}: {row_preview}")
    
    # Check if this looks like a header row (all strings, no dates/numbers)
    if all(isinstance(cell, str) for cell in row_preview if cell is not None):
        print(f"  ^ Likely HEADER row")
