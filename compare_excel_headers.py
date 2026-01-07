"""Compare Excel file structures to understand header patterns"""
import openpyxl
import pandas as pd
from pathlib import Path

files = {
    'zrsd004': 'demodata/zrsd004.XLSX',
    'zrsd002': 'demodata/zrsd002.XLSX',
    'mb51': 'demodata/mb51.XLSX'
}

for name, file_path in files.items():
    if not Path(file_path).exists():
        print(f"SKIP: {name} - file not found")
        continue
        
    print(f"\n{'=' * 80}")
    print(f"{name.upper()}: {file_path}")
    print('=' * 80)
    
    try:
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        
        # Check first 3 rows
        for i in range(1, 4):
            row_vals = [cell.value for cell in ws[i]]
            # Show first 8 values
            preview = str(row_vals[:8])
            if len(preview) > 100:
                preview = preview[:97] + '...'
            print(f"Row {i}: {preview}")
        
        # Test pandas reading
        print(f"\nPandas with header=0:")
        df = pd.read_excel(file_path, header=0, nrows=1)
        print(f"  Columns: {df.columns.tolist()[:5]}")
        
    except Exception as e:
        print(f"ERROR: {e}")
