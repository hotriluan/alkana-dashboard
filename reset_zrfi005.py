#!/usr/bin/env python3
"""
Reset ZRFI005 data and reload
"""
from datetime import date
from src.db.connection import SessionLocal
from src.db.models import RawZrfi005, FactArAging

db = SessionLocal()

# Delete 07/01 and after (incomplete data)
deleted_raw = db.query(RawZrfi005).filter(
    RawZrfi005.snapshot_date >= date(2026, 1, 7)
).delete(synchronize_session=False)

deleted_fact = db.query(FactArAging).filter(
    FactArAging.snapshot_date >= date(2026, 1, 7)
).delete(synchronize_session=False)

db.commit()

print(f"\n✓ Deleted {deleted_raw} raw records from 07/01 onwards")
print(f"✓ Deleted {deleted_fact} fact records from 07/01 onwards")
print(f"\n📝 Now please re-upload ZRFI005 file for 07/01/2026")

db.close()
