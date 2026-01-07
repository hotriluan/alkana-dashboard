#!/usr/bin/env python3
"""
Check ZRFI005 file structure
"""
import pandas as pd
from pathlib import Path

excel_file = Path("demodata/ZRFI005.XLSX")

print(f"\n📊 Checking {excel_file}...")

df = pd.read_excel(excel_file, header=0, dtype=str)

print(f"   Rows: {len(df)}")
print(f"   Columns: {len(df.columns)}")
print(f"   Column names: {list(df.columns)}")

# Check for null values
print("\n   Null value check:")
null_counts = df.isnull().sum()
for col in df.columns:
    if null_counts[col] > 0:
        print(f"      {col}: {null_counts[col]} nulls")

# Show first 5 rows
print("\n   First 5 rows:")
print(df[['Customer Name', 'Salesman Name', 'Total Target', 'Total Realization']].head())

# Check customer count
print(f"\n   Unique customers: {df['Customer Name'].nunique()}")
