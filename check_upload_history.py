#!/usr/bin/env python3
"""
Check upload history
"""
from src.db.connection import SessionLocal
from src.db.models import UploadHistory

db = SessionLocal()

uploads = db.query(UploadHistory).filter(
    UploadHistory.file_type == 'ZRFI005'
).order_by(UploadHistory.id.desc()).all()

print(f"\n📋 ZRFI005 Upload History:")
print("=" * 100)

for u in uploads:
    print(f"\nUpload ID: {u.id}")
    print(f"  Status: {u.status}")
    print(f"  File: {u.file_name}")
    print(f"  Snapshot: {u.snapshot_date}")
    print(f"  Loaded: {u.rows_loaded} | Updated: {u.rows_updated} | Skipped: {u.rows_skipped} | Failed: {u.rows_failed}")
    if u.error_message:
        print(f"  Error: {u.error_message}")

db.close()
