#!/usr/bin/env python3
"""
Direct database check - bypassing auth
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Set Django/FastAPI settings
os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://admin:admin@localhost:5432/alkana_data"))

try:
    from sqlalchemy import create_engine, func, text, inspect
    from sqlalchemy.orm import sessionmaker
    from dotenv import load_dotenv
    import os
    
    # Load environment variables
    load_dotenv()
    
    # Create engine directly
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password123@localhost:5432/alkana_dashboard")
    print(f"Connecting to: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Test connection
    result = session.execute(text("SELECT 1"))
    print("✅ Database connected\n")
    
    # Check raw_zrfi005 table
    print("=" * 80)
    print("📊 RAW_ZRFI005 TABLE STATUS")
    print("=" * 80)
    
    # Check if table exists
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'raw_zrfi005' not in tables:
        print("❌ Table raw_zrfi005 does NOT exist")
    else:
        print("✅ Table raw_zrfi005 exists")
        
        # Get column info
        columns = inspector.get_columns('raw_zrfi005')
        print(f"\nColumns: {len(columns)}")
        
        # Count records
        count_result = session.execute(text("SELECT COUNT(*) FROM raw_zrfi005"))
        total_count = count_result.scalar()
        print(f"Total Records: {total_count}")
        
        # Count by snapshot
        print("\nRecords by Snapshot Date:")
        snap_result = session.execute(text("""
            SELECT snapshot_date, COUNT(*) as cnt 
            FROM raw_zrfi005 
            GROUP BY snapshot_date 
            ORDER BY snapshot_date DESC
        """))
        
        for row in snap_result:
            print(f"  {row[0]}: {row[1]} records")
        
        # Check for hash duplicates
        print("\n✓ Checking for Row Hash Collisions:")
        collision_result = session.execute(text("""
            SELECT snapshot_date, COUNT(*) as total, COUNT(DISTINCT row_hash) as unique_hashes
            FROM raw_zrfi005
            GROUP BY snapshot_date
            ORDER BY snapshot_date DESC
        """))
        
        for row in collision_result:
            snapshot, total, unique = row
            if total == unique:
                print(f"  ✅ {snapshot}: {total} records, {unique} unique hashes (NO collision)")
            else:
                print(f"  ❌ {snapshot}: {total} records, {unique} unique hashes ({total - unique} collisions!)")
        
        # Sample records
        print("\n✓ Sample Records (last 10):")
        sample_result = session.execute(text("""
            SELECT snapshot_date, customer_name, row_hash 
            FROM raw_zrfi005 
            ORDER BY snapshot_date DESC, customer_name 
            LIMIT 10
        """))
        
        for row in sample_result:
            snapshot, customer, hash_val = row
            print(f"  {snapshot} | {customer[:30]:30} | {hash_val[:16]}...")
    
    # Check fact_ar_aging
    print("\n" + "=" * 80)
    print("📊 FACT_AR_AGING TABLE STATUS")
    print("=" * 80)
    
    if 'fact_ar_aging' not in tables:
        print("❌ Table fact_ar_aging does NOT exist")
    else:
        print("✅ Table fact_ar_aging exists")
        
        # Count records
        count_result = session.execute(text("SELECT COUNT(*) FROM fact_ar_aging"))
        total_count = count_result.scalar()
        print(f"Total Records: {total_count}")
        
        # Count by snapshot
        print("\nRecords by Snapshot Date:")
        snap_result = session.execute(text("""
            SELECT snapshot_date, COUNT(*) as cnt 
            FROM fact_ar_aging 
            GROUP BY snapshot_date 
            ORDER BY snapshot_date DESC
        """))
        
        for row in snap_result:
            print(f"  {row[0]}: {row[1]} records")
    
    # Check upload history
    print("\n" + "=" * 80)
    print("📊 UPLOAD_HISTORY TABLE")
    print("=" * 80)
    
    if 'upload_history' not in tables:
        print("❌ Table upload_history does NOT exist")
    else:
        print("✅ Table upload_history exists")
        
        # Get latest uploads
        hist_result = session.execute(text("""
            SELECT upload_id, filename, snapshot_date, status, rows_loaded, rows_updated, rows_skipped, rows_failed
            FROM upload_history
            ORDER BY upload_id DESC
            LIMIT 5
        """))
        
        print("\nLatest 5 Uploads:")
        for row in hist_result:
            upload_id, filename, snapshot, status, loaded, updated, skipped, failed = row
            print(f"\n  Upload ID: {upload_id}")
            print(f"    File: {filename}")
            print(f"    Snapshot: {snapshot}")
            print(f"    Status: {status}")
            print(f"    Loaded: {loaded} | Updated: {updated} | Skipped: {skipped} | Failed: {failed}")
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 SUMMARY")
    print("=" * 80)
    
    raw_count = session.execute(text("SELECT COUNT(*) FROM raw_zrfi005")).scalar()
    fact_count = session.execute(text("SELECT COUNT(*) FROM fact_ar_aging")).scalar()
    
    if raw_count >= 98:
        print(f"✅ Raw table has {raw_count} records (>= 98 expected)")
    else:
        print(f"❌ Raw table has only {raw_count} records (expected >= 98)")
    
    if fact_count >= 98:
        print(f"✅ Fact table has {fact_count} records (>= 98 expected)")
    else:
        print(f"❌ Fact table has only {fact_count} records (expected >= 98)")
    
    session.close()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
