"""
Import zrsd006.XLSX to populate raw_zrsd006 with distribution channel data
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from sqlalchemy.orm import Session
from src.db.connection import get_db
from src.db.models import RawZrsd006

# Read Excel file
print("Reading zrsd006.XLSX...")
df = pd.read_excel('demodata/zrsd006.XLSX')

print(f"Loaded {len(df)} rows")
print(f"Columns: {list(df.columns)}")
print("\nFirst few rows:")
print(df.head(3))

# Check for distribution channel column
dist_col = None
for col in df.columns:
    if 'distribution' in col.lower() or 'channel' in col.lower():
        dist_col = col
        print(f"\n✅ Found distribution channel column: '{col}'")
        break

# Check for material code column  
mat_col = None
for col in df.columns:
    if 'material' in col.lower() and 'code' in col.lower():
        mat_col = col
        print(f"✅ Found material code column: '{col}'")
        break

if not mat_col:
    # Try just 'Material'
    for col in df.columns:
        if col.lower() == 'material' or 'material code' in col.lower():
            mat_col = col
            print(f"✅ Found material column: '{col}'")
            break

print(f"\nDistribution channel values:")
if dist_col:
    print(df[dist_col].value_counts())
else:
    print("❌ No distribution channel column found!")

print(f"\nSample material codes:")
if mat_col:
    print(df[mat_col].head(10).tolist())
else:
    print("❌ No material code column found!")
