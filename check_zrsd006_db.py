#!/usr/bin/env python3
"""Check ZRSD006 in database"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.session import SessionLocal
from src.db.models import RawZrsd006
import pandas as pd

db = SessionLocal()

# Check database count
db_count = db.query(RawZrsd006).count()
print(f"Total RawZrsd006 records in database: {db_count}")

# Check Excel files
excel_files = ['demodata/11.XLSX', 'demodata/12.XLSX', 'demodata/13.XLSX', 'demodata/15.XLSX']
total_excel_rows = 0

print("\nExcel files:")
for file in excel_files:
    p = Path(file)
    if p.exists():
        df = pd.read_excel(p, dtype=str)
        total_excel_rows += len(df)
        print(f"  {file}: {len(df)} rows")
    else:
        print(f"  {file}: NOT FOUND")

print(f"\nTotal rows in Excel (11+12+13+15): {total_excel_rows}")

if db_count == 0:
    print("\n✓ Database EMPTY → Upload should LOAD all rows")
    print(f"  Expected loaded: {total_excel_rows}")
    print(f"  Actual loaded: 0")
    print("  ❌ BUG: Why skip? All rows should be loaded!")
elif db_count == total_excel_rows:
    print("\n✓ Database has ALL rows → Skip is CORRECT (duplicates)")
    print("  All rows from Excel are already in DB")
else:
    print(f"\n⚠️ Partial: {db_count} in DB vs {total_excel_rows} in Excel")

# Show sample from DB
if db_count > 0:
    print("\nSample records in database (first 3):")
    for rec in db.query(RawZrsd006).limit(3):
        print(f"  Material: {rec.material}, Dist Channel: {rec.dist_channel}")

db.close()
