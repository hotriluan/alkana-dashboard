#!/usr/bin/env python3
"""
Final reset - remove 6 wrong records and allow clean upload
"""
from datetime import date
from src.db.connection import SessionLocal
from src.db.models import RawZrfi005, FactArAging

db = SessionLocal()

# Delete 07/01 records
deleted_raw = db.query(RawZrfi005).filter(
    RawZrfi005.snapshot_date == date(2026, 1, 7)
).delete(synchronize_session=False)

deleted_fact = db.query(FactArAging).filter(
    FactArAging.snapshot_date == date(2026, 1, 7)
).delete(synchronize_session=False)

db.commit()

print(f"\n✓ Reset complete!")
print(f"  Deleted {deleted_raw} raw records from 07/01")
print(f"  Deleted {deleted_fact} fact records from 07/01")
print(f"\n📝 Code fix applied:")
print(f"  - row_hash now includes snapshot_date")
print(f"  - Each snapshot will have unique hashes")
print(f"\n📤 Ready for re-upload!")

db.close()
