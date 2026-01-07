"""
Test ZRFI005 loader fix - verify column name mapping

Run with:
    python test_zrfi005_fix.py

Skills: data-validation, debugging
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
from pathlib import Path
from datetime import date

# Import loader
from src.etl.loaders import Zrfi005Loader
from src.db.connection import SessionLocal

print("=" * 70)
print("TEST: ZRFI005 Loader Column Mapping Fix")
print("=" * 70)

# Test 1: Check Excel file columns
print("\n1. Checking Excel file structure...")
file_path = Path("demodata/ZRFI005.XLSX")
if not file_path.exists():
    print(f"❌ File not found: {file_path}")
    sys.exit(1)

df = pd.read_excel(file_path, header=0, nrows=3)
print(f"✓ File found: {len(df)} rows, {len(df.columns)} columns")
print(f"\nExpected columns in loader:")
expected_cols = [
    'Distribution Channel',
    'Customer Group',  # Fixed from 'Cust. Group'
    'Salesman Name',
    'Customer Name',
    'Currency',  # Fixed from 'Curr'
    'Target 1-30 Days',
    'Target 31-60 Days',
    'Target 61 - 90 Days',  # Fixed: added spaces
    'Target 91 - 120 Days',  # Fixed: added spaces
    'Target 121 - 180 Days',  # Fixed: added spaces
    'Target > 180 Days',
    'Total Target',
    'Realization Not Due',
    'Realization 1 - 30 Days',  # Fixed: added spaces
    'Realization 31 - 60 Days',  # Fixed: added spaces
    'Realization 61 - 90 Days',  # Fixed: added spaces
    'Realization 91 - 120 Days',  # Fixed: added spaces
    'Realization 121 - 180 Days',  # Fixed: added spaces
    'Realization > 180 Days',
    'Total Realization'
]

actual_cols = list(df.columns)
print("\nColumn matching check:")
missing = []
for col in expected_cols:
    if col in actual_cols:
        print(f"  ✓ {col}")
    else:
        print(f"  ❌ {col} (NOT FOUND)")
        missing.append(col)

if missing:
    print(f"\n❌ Missing columns: {missing}")
    print("\nActual columns in file:")
    for col in actual_cols:
        print(f"  - {col}")
    sys.exit(1)
else:
    print("\n✅ All expected columns found!")

# Test 2: Load data with loader
print("\n2. Testing loader...")
db = SessionLocal()
try:
    loader = Zrfi005Loader(db, mode='upsert', file_path=file_path)
    
    # Use today's date as snapshot
    snapshot_date = date.today()
    print(f"Loading with snapshot_date={snapshot_date}...")
    
    stats = loader.load(snapshot_date=snapshot_date)
    
    print(f"\n✅ Load completed!")
    print(f"  Loaded: {stats.get('loaded', 0)}")
    print(f"  Updated: {stats.get('updated', 0)}")
    print(f"  Skipped: {stats.get('skipped', 0)}")
    print(f"  Errors: {stats.get('errors', 0)}")
    
    if stats.get('errors', 0) > 0:
        print(f"\n⚠ Warning: {stats['errors']} rows had errors")
    else:
        print(f"\n✅ SUCCESS: No errors!")
        
finally:
    db.close()

print("\n" + "=" * 70)
print("Test completed!")
print("=" * 70)
