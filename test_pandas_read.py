#!/usr/bin/env python3
"""Test pandas read_excel with different settings"""
import pandas as pd
from pathlib import Path

file_path = Path('demodata/11.XLSX')

print("Test 1: Default read_excel")
df1 = pd.read_excel(file_path)
print(f"  Shape: {df1.shape}")
print(f"  Columns: {list(df1.columns)[:5]}")

print("\nTest 2: read_excel with header=0")
df2 = pd.read_excel(file_path, header=0)
print(f"  Shape: {df2.shape}")
print(f"  Columns: {list(df2.columns)[:5]}")

print("\nTest 3: read_excel with engine='openpyxl'")
df3 = pd.read_excel(file_path, header=0, engine='openpyxl')
print(f"  Shape: {df3.shape}")
print(f"  Columns: {list(df3.columns)[:5]}")

print("\nTest 4: read_excel with sheet_name=0")
df4 = pd.read_excel(file_path, sheet_name=0, header=0)
print(f"  Shape: {df4.shape}")
print(f"  Columns: {list(df4.columns)[:5]}")

print("\nTest 5: Check first row of df2")
print(f"  First row: {df2.iloc[0, :3].tolist()}")
