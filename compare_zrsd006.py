#!/usr/bin/env python3
"""
Compare ZRSD006 data: Database vs Excel files
Check if skip is correct or a bug
"""
import pandas as pd
from pathlib import Path
from src.db.session import SessionLocal
from src.db.models import RawZrsd006
from src.core.utils import compute_row_hash, row_to_json, safe_str
import json

db = SessionLocal()

# Excel files to check
excel_files = [
    'demodata/11.XLSX',
    'demodata/12.XLSX',
    'demodata/13.XLSX',
    'demodata/15.XLSX'
]

print("="*80)
print("ZRSD006 DATABASE vs EXCEL COMPARISON")
print("="*80)

# Check database
print("\n[DATABASE] RawZrsd006 Records:")
db_records = db.query(RawZrsd006).all()
print(f"Total in DB: {len(db_records)}")

if db_records:
    # Show sample of business keys
    print("\nBusiness keys (Material + Dist Channel) in DB:")
    sample_keys = set()
    for rec in db_records[:10]:
        key = f"{rec.material} + {rec.dist_channel}"
        sample_keys.add(key)
        print(f"  - {key}")
    
    if len(db_records) > 10:
        print(f"  ... and {len(db_records) - 10} more")

# Check Excel files
print("\n" + "="*80)
for excel_file in excel_files:
    file_path = Path(excel_file)
    if not file_path.exists():
        print(f"\n❌ {excel_file} - NOT FOUND")
        continue
    
    print(f"\n[EXCEL] {excel_file}:")
    df = pd.read_excel(file_path, header=0, dtype=str)
    print(f"  Total rows: {len(df)}")
    
    # Get business keys
    print(f"  Business keys (Material Code + Distribution Channel):")
    excel_keys = set()
    for idx, row in df.iterrows():
        material = safe_str(row.get('Material Code'))
        dist_channel = safe_str(row.get('Distribution Channel'))
        key = f"{material} + {dist_channel}"
        excel_keys.add(key)
        
        if idx < 5:  # Show first 5
            print(f"    - {key}")
    
    if len(df) > 5:
        print(f"    ... and {len(df) - 5} more")
    
    # Compare with DB
    print(f"\n  Comparison with Database:")
    in_db = 0
    not_in_db = 0
    
    for key in excel_keys:
        material, dist_channel = key.split(' + ')
        existing = db.query(RawZrsd006).filter_by(
            material=material,
            dist_channel=dist_channel
        ).first()
        
        if existing:
            in_db += 1
        else:
            not_in_db += 1
    
    print(f"    ✓ Keys already in DB: {in_db}")
    print(f"    ✗ Keys NOT in DB: {not_in_db}")
    print(f"    → Should load: {not_in_db} records")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)

total_in_db = len(db.query(RawZrsd006).all())
total_in_excel = sum([len(pd.read_excel(f, dtype=str)) for f in excel_files if Path(f).exists()])

print(f"\nDatabase RawZrsd006: {total_in_db} records")
print(f"Excel files (11+12+13+15): {total_in_excel} rows")

if total_in_db == 0:
    print("\n✓ Database is EMPTY → Upload should LOAD all rows, not skip")
elif total_in_db == total_in_excel:
    print("\n✓ Database has ALL rows → Skip is CORRECT")
else:
    print(f"\n⚠️ Partial match: {total_in_db} in DB vs {total_in_excel} in Excel")
    print("   → Check for duplicate detection or filtering logic")

db.close()
