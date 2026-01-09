#!/usr/bin/env python3
"""
🔍 Verify ZRFI005 fix is working correctly
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.database import SessionLocal, engine
from src.models.schemas import RawZrfi005, UploadHistory, FactArAging
from sqlalchemy import func, inspect
from datetime import datetime
import json

print("=" * 80)
print("🔍 ZRFI005 FIX VERIFICATION")
print("=" * 80)

db = SessionLocal()

try:
    # Check 1: Code verification
    print("\n✓ STEP 1: Code Verification")
    print("-" * 80)
    print("Checking loaders.py line 749 for snapshot_date in row_hash...")
    
    loaders_path = Path(__file__).parent / "src/etl/loaders.py"
    with open(loaders_path) as f:
        lines = f.readlines()
        line_749 = lines[748].strip()  # 0-indexed
        
    if 'snapshot_date' in line_749:
        print("✅ VERIFIED: snapshot_date IS included in row_hash calculation")
        print(f"   Code: {line_749[:100]}...")
    else:
        print("❌ ERROR: snapshot_date NOT found in row_hash")
        print(f"   Code: {line_749}")
    
    # Check 2: Database state
    print("\n✓ STEP 2: Database State Analysis")
    print("-" * 80)
    
    # Count records per snapshot
    snapshot_counts = db.query(
        RawZrfi005.snapshot_date,
        func.count(RawZrfi005.id).label('count')
    ).group_by(RawZrfi005.snapshot_date).all()
    
    print("Records by Snapshot Date:")
    total_records = 0
    for snapshot, count in snapshot_counts:
        print(f"  {snapshot}: {count} records")
        total_records += count
    print(f"  TOTAL: {total_records} records")
    
    # Check 3: Upload history
    print("\n✓ STEP 3: Latest Upload History")
    print("-" * 80)
    
    latest_uploads = db.query(UploadHistory).order_by(
        UploadHistory.upload_id.desc()
    ).limit(3).all()
    
    for upload in latest_uploads:
        print(f"\nUpload ID: {upload.upload_id}")
        print(f"  File: {upload.filename}")
        print(f"  Snapshot: {upload.snapshot_date}")
        print(f"  Status: {upload.status}")
        print(f"  Loaded: {upload.rows_loaded} | Updated: {upload.rows_updated} | Skipped: {upload.rows_skipped} | Failed: {upload.rows_failed}")
    
    # Check 4: Hash uniqueness per snapshot
    print("\n✓ STEP 4: Row Hash Uniqueness (Critical Check)")
    print("-" * 80)
    
    for snapshot, count in snapshot_counts:
        unique_hashes = db.query(func.count(func.distinct(RawZrfi005.row_hash))).filter(
            RawZrfi005.snapshot_date == snapshot
        ).scalar()
        
        print(f"{snapshot}: {count} records, {unique_hashes} unique hashes", end="")
        if count == unique_hashes:
            print(" ✅ All unique")
        else:
            print(f" ❌ COLLISION: {count - unique_hashes} duplicates!")
    
    # Check 5: Fact table
    print("\n✓ STEP 5: Fact Table (fact_ar_aging)")
    print("-" * 80)
    
    fact_counts = db.query(
        FactArAging.snapshot_date,
        func.count(FactArAging.id).label('count')
    ).group_by(FactArAging.snapshot_date).all()
    
    if fact_counts:
        for snapshot, count in fact_counts:
            print(f"  {snapshot}: {count} fact records")
    else:
        print("  No fact records yet")
    
    # Check 6: Specific sample hashes
    print("\n✓ STEP 6: Sample Record Verification")
    print("-" * 80)
    
    # Get samples from different snapshots
    samples = db.query(
        RawZrfi005.snapshot_date,
        RawZrfi005.customer_name,
        RawZrfi005.row_hash
    ).order_by(RawZrfi005.snapshot_date, RawZrfi005.customer_name).limit(10).all()
    
    if samples:
        for snapshot, customer, row_hash in samples:
            print(f"  {snapshot} | {customer[:30]:30} | {row_hash[:16]}...")
    
    # Check 7: Status summary
    print("\n" + "=" * 80)
    print("📊 STATUS SUMMARY")
    print("=" * 80)
    
    if total_records >= 98:
        print("✅ PASS: Database has sufficient records (>= 98)")
    else:
        print(f"❌ FAIL: Database has {total_records} records (expected >= 98)")
    
    if 'snapshot_date' in line_749:
        print("✅ PASS: Code includes snapshot_date in row_hash")
    else:
        print("❌ FAIL: Code missing snapshot_date in row_hash")
    
    if latest_uploads:
        latest = latest_uploads[0]
        if latest.rows_loaded > 0:
            print(f"✅ PASS: Latest upload loaded {latest.rows_loaded} records")
        else:
            print(f"❌ FAIL: Latest upload loaded 0 records (all skipped: {latest.rows_skipped})")
    
    print("\n🎯 NEXT STEPS:")
    print("1. If records < 98: Check if new upload was processed after code fix")
    print("2. If codes match: Manual re-upload in UI to trigger fresh load")
    print("3. Run this script again to verify post-upload results")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
