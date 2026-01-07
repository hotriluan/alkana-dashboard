#!/usr/bin/env python3
"""
Claude Kit Engineer - Investigation Phase
Debug ZRFI005 upload and data aggregation
"""
from datetime import date
from src.db.connection import SessionLocal
from src.db.models import RawZrfi005, FactArAging, UploadHistory

def investigate():
    db = SessionLocal()
    target_date = date(2026, 1, 7)
    
    print("\n" + "="*100)
    print("🔍 CLAUDE KIT ENGINEER - INVESTIGATION PHASE")
    print("="*100)
    
    # 1. Check upload history
    print("\n[STEP 1] Upload History for 2026-01-07")
    print("-" * 100)
    
    uploads = db.query(UploadHistory).filter(
        UploadHistory.file_type == 'ZRFI005',
        UploadHistory.snapshot_date == target_date
    ).order_by(UploadHistory.id.desc()).all()
    
    if uploads:
        latest = uploads[0]
        print(f"✓ Latest upload ID: {latest.id}")
        print(f"  Status: {latest.status}")
        print(f"  File: {latest.file_name}")
        print(f"  Loaded: {latest.rows_loaded} | Updated: {latest.rows_updated} | Skipped: {latest.rows_skipped} | Failed: {latest.rows_failed}")
        print(f"  Total: {latest.rows_loaded + latest.rows_updated + latest.rows_skipped}")
        
        if latest.error_message:
            print(f"  ❌ ERROR: {latest.error_message[:200]}")
    else:
        print("❌ NO UPLOADS FOUND FOR 07/01/2026")
    
    # 2. Check raw data
    print("\n[STEP 2] Raw Data (raw_zrfi005) for 2026-01-07")
    print("-" * 100)
    
    raw_count = db.query(RawZrfi005).filter(
        RawZrfi005.snapshot_date == target_date
    ).count()
    
    raw_records = db.query(RawZrfi005).filter(
        RawZrfi005.snapshot_date == target_date
    ).all()
    
    print(f"✓ Total raw records: {raw_count}")
    
    if raw_count > 0:
        total_target = sum(r.total_target or 0 for r in raw_records)
        total_real = sum(r.total_realization or 0 for r in raw_records)
        
        print(f"  Total Target: {total_target:,.0f}")
        print(f"  Total Realization: {total_real:,.0f}")
        print(f"  Collection Rate: {(total_real/total_target*100 if total_target else 0):.1f}%")
        print(f"  Expected: 415.4M target, 243.2M realization (58.5%)")
        
        if total_target > 50000000000:  # > 50B expected
            print(f"  ❌ DATA MISMATCH: Expected ~415B, got {total_target/1000000000:.1f}B")
    else:
        print("  ❌ NO RAW RECORDS - Upload failed or not executed")
    
    # 3. Check fact data
    print("\n[STEP 3] Fact Data (fact_ar_aging) for 2026-01-07")
    print("-" * 100)
    
    fact_count = db.query(FactArAging).filter(
        FactArAging.snapshot_date == target_date
    ).count()
    
    fact_records = db.query(FactArAging).filter(
        FactArAging.snapshot_date == target_date
    ).all()
    
    print(f"✓ Total fact records: {fact_count}")
    
    if fact_count > 0:
        total_target = sum(r.total_target or 0 for r in fact_records)
        total_real = sum(r.total_realization or 0 for r in fact_records)
        
        print(f"  Total Target: {total_target:,.0f}")
        print(f"  Total Realization: {total_real:,.0f}")
        
        if fact_count < 10:
            print(f"  ⚠️  LOW COUNT: {fact_count} records (expected ~98)")
    else:
        print("  ❌ NO FACT RECORDS - Transform not executed")
    
    # 4. Compare raw vs fact
    print("\n[STEP 4] Data Consistency Check")
    print("-" * 100)
    
    if raw_count > 0 and fact_count > 0:
        raw_total_target = sum(r.total_target or 0 for r in raw_records)
        fact_total_target = sum(r.total_target or 0 for r in fact_records)
        
        print(f"Raw records:  {raw_count}")
        print(f"Fact records: {fact_count}")
        
        if raw_total_target == fact_total_target:
            print(f"✓ Data matches: {raw_total_target:,.0f}")
        else:
            print(f"❌ DATA MISMATCH!")
            print(f"   Raw:  {raw_total_target:,.0f}")
            print(f"   Fact: {fact_total_target:,.0f}")
            print(f"   Lost: {raw_total_target - fact_total_target:,.0f}")
    
    # 5. Check DB source file
    print("\n[STEP 5] Source Files in Database")
    print("-" * 100)
    
    source_files = db.query(RawZrfi005.source_file).filter(
        RawZrfi005.snapshot_date == target_date
    ).distinct().all()
    
    if source_files:
        for sf in source_files:
            count = db.query(RawZrfi005).filter(
                RawZrfi005.snapshot_date == target_date,
                RawZrfi005.source_file == sf[0]
            ).count()
            print(f"✓ {sf[0]}: {count} records")
    else:
        print("❌ NO SOURCE FILES - No data loaded")
    
    # 6. Recommendations
    print("\n[STEP 6] Diagnostic Summary & Recommendations")
    print("-" * 100)
    
    if raw_count == 0:
        print("❌ ISSUE: No raw data loaded from upload")
        print("   ACTION: Check upload endpoint, file processing logic")
    elif raw_count < 98:
        print(f"⚠️  ISSUE: Incomplete data - {raw_count}/98 records")
        print("   ACTION: Check if upsert skipped records, or loader stopped early")
    elif fact_count == 0:
        print("❌ ISSUE: Raw data exists but fact table empty")
        print("   ACTION: Check transformer.transform_zrfi005() execution")
    elif fact_count < raw_count:
        print(f"⚠️  ISSUE: Data loss - raw {raw_count}, fact {fact_count}")
        print("   ACTION: Check filtering in transform logic")
    else:
        print("✓ Data looks complete - might be display/calculation issue in frontend")
    
    print("\n" + "="*100 + "\n")
    
    db.close()

if __name__ == '__main__':
    investigate()
