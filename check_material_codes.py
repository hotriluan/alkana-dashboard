#!/usr/bin/env python3
"""Check ZRSD006 Material Code column for issues"""
import pandas as pd
from pathlib import Path

excel_files = ['demodata/11.XLSX', 'demodata/12.XLSX', 'demodata/13.XLSX', 'demodata/15.XLSX']

for file in excel_files:
    p = Path(file)
    if not p.exists():
        print(f"❌ {file} not found")
        continue
    
    print(f"\n{'='*60}")
    print(f"📄 {p.name}")
    print('='*60)
    
    df = pd.read_excel(p, dtype=str)
    print(f"Total rows: {len(df)}")
    
    # Check Material Code column
    mat_col = df.get('Material Code')
    if mat_col is None:
        print("❌ 'Material Code' column NOT found")
        print(f"Columns: {list(df.columns)[:10]}")
        continue
    
    print(f"\n'Material Code' column analysis:")
    
    # Count nulls
    nulls = mat_col.isna().sum()
    print(f"  Null/NaN values: {nulls}")
    
    # Show sample values
    print(f"\n  Sample Material Codes (first 5 rows):")
    for idx in range(min(5, len(df))):
        val = mat_col.iloc[idx]
        if pd.isna(val):
            print(f"    Row {idx+2}: [NaN]")
        else:
            val_str = str(val).strip()
            val_lstrip = val_str.lstrip('0')
            if val_lstrip:
                print(f"    Row {idx+2}: '{val_str}' → lstrip('0'): '{val_lstrip}' ✓")
            else:
                print(f"    Row {idx+2}: '{val_str}' → lstrip('0'): [EMPTY] ❌")
    
    # Count rows that would be skipped
    empty_codes = 0
    becomes_empty = 0
    
    for val in mat_col.dropna():
        val_str = str(val).strip()
        if not val_str:
            empty_codes += 1
        elif not val_str.lstrip('0'):
            becomes_empty += 1
    
    print(f"\n  Skip analysis:")
    print(f"    Already empty: {empty_codes}")
    print(f"    Becomes empty after lstrip('0'): {becomes_empty}")
    print(f"    Should SKIP: {empty_codes + becomes_empty} rows")
    print(f"    Should LOAD: {len(df) - nulls - empty_codes - becomes_empty} rows")
