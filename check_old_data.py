#!/usr/bin/env python3
"""
Check where the old data 6 records came from
"""
from datetime import date
from src.db.connection import SessionLocal
from src.db.models import RawZrfi005

db = SessionLocal()

print("\n🔍 Checking source of 6 records for 07/01...")

records = db.query(RawZrfi005).filter(
    RawZrfi005.snapshot_date == date(2026, 1, 7)
).all()

for r in records:
    print(f"\nCustomer: {r.customer_name}")
    print(f"  Source: {r.source_file}")
    print(f"  Row Hash: {r.row_hash}")
    print(f"  Target: {r.total_target}")

# Check all snapshots
print("\n\n📊 All snapshots in DB:")
snapshots = db.query(RawZrfi005.snapshot_date).distinct().order_by(RawZrfi005.snapshot_date.desc()).all()

for snap in snapshots:
    count = db.query(RawZrfi005).filter(RawZrfi005.snapshot_date == snap[0]).count()
    print(f"  {snap[0]}: {count} records")

db.close()
