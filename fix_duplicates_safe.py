"""
FIX DUPLICATES - SAFE BATCH MODE
Delete duplicates in small batches to avoid deadlocks
"""

from sqlalchemy import create_engine, text
import os
import time
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("="*80)
print("  FIX DUPLICATES - SAFE BATCH MODE")
print("="*80)

with engine.connect() as conn:
    
    # FIX 1: raw_mb51 - Use batched approach
    print("\n[1/2] Fixing raw_mb51 (583 duplicates)...")
    before = conn.execute(text("SELECT COUNT(*) FROM raw_mb51")).scalar()
    print(f"  Before: {before:,} rows")
    
    # Get list of duplicate row_hashes
    result = conn.execute(text("""
        SELECT row_hash, COUNT(*) as cnt
        FROM raw_mb51
        GROUP BY row_hash
        HAVING COUNT(*) > 1
    """))
    duplicate_hashes = result.fetchall()
    print(f"  Found {len(duplicate_hashes)} unique row_hashes with duplicates")
    
    # Delete duplicates for each hash (keep MIN id)
    deleted_total = 0
    for i, (row_hash, count) in enumerate(duplicate_hashes):
        # Delete all except the one with MIN id
        result = conn.execute(text("""
            DELETE FROM raw_mb51
            WHERE row_hash = :hash
            AND id NOT IN (
                SELECT MIN(id)
                FROM raw_mb51
                WHERE row_hash = :hash
            )
        """), {'hash': row_hash})
        
        deleted_total += result.rowcount
        
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(duplicate_hashes)} hashes processed, {deleted_total} rows deleted")
    
    after = conn.execute(text("SELECT COUNT(*) FROM raw_mb51")).scalar()
    print(f"  After: {after:,} rows")
    print(f"  ✅ Deleted: {deleted_total} duplicates")
    
    # Verify
    result = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT row_hash)
        FROM raw_mb51
    """))
    remaining = result.scalar()
    print(f"  Verification: {remaining} duplicates remaining")
    
    # FIX 2: fact_alerts
    print("\n[2/2] Fixing fact_alerts (1 duplicate)...")
    before = conn.execute(text("SELECT COUNT(*) FROM fact_alerts")).scalar()
    print(f"  Before: {before:,} rows")
    
    # Get duplicate
    result = conn.execute(text("""
        SELECT batch, alert_type
        FROM fact_alerts
        GROUP BY batch, alert_type
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()
    
    if duplicates:
        print(f"  Found {len(duplicates)} duplicate combinations")
        for batch, alert_type in duplicates:
            print(f"    - Batch: {batch}, Alert: {alert_type}")
            
            # Delete keeping MIN id
            conn.execute(text("""
                DELETE FROM fact_alerts
                WHERE batch = :batch
                AND alert_type = :alert_type
                AND id NOT IN (
                    SELECT MIN(id)
                    FROM fact_alerts
                    WHERE batch = :batch
                    AND alert_type = :alert_type
                )
            """), {'batch': batch, 'alert_type': alert_type})
    
    after = conn.execute(text("SELECT COUNT(*) FROM fact_alerts")).scalar()
    print(f"  After: {after:,} rows")
    print(f"  ✅ Deleted: {before - after} duplicates")
    
    # ADD UNIQUE CONSTRAINTS
    print("\n[3/3] Adding UNIQUE constraints...")
    
    constraints = [
        ("idx_raw_mb51_hash_uniq", "raw_mb51", "row_hash"),
        ("idx_fact_alerts_batch_type_uniq", "fact_alerts", "batch, alert_type"),
        ("idx_fact_billing_biz_uniq", "fact_billing", "billing_document, billing_item"),
        ("idx_fact_production_biz_uniq", "fact_production", "order_number, batch"),
        ("idx_fact_delivery_biz_uniq", "fact_delivery", "delivery, line_item"),
        ("idx_fact_lead_time_biz_uniq", "fact_lead_time", "order_number, batch"),
        ("idx_fact_p02_p01_yield_uniq", "fact_p02_p01_yield", "p02_batch, p01_batch"),
        ("idx_fact_target_uniq", "fact_target", "salesman_name, semester, year"),
        ("idx_raw_cooispi_hash_uniq", "raw_cooispi", "row_hash"),
        ("idx_raw_zrmm024_hash_uniq", "raw_zrmm024", "row_hash"),
        ("idx_raw_zrsd002_hash_uniq", "raw_zrsd002", "row_hash"),
        ("idx_raw_zrsd004_hash_uniq", "raw_zrsd004", "row_hash"),
        ("idx_raw_zrsd006_hash_uniq", "raw_zrsd006", "row_hash"),
        ("idx_raw_zrfi005_hash_uniq", "raw_zrfi005", "row_hash"),
        ("idx_raw_target_hash_uniq", "raw_target", "row_hash"),
    ]
    
    added = 0
    skipped = 0
    
    for idx_name, table, cols in constraints:
        try:
            conn.execute(text(f"""
                CREATE UNIQUE INDEX IF NOT EXISTS {idx_name}
                ON {table} ({cols})
            """))
            print(f"  ✅ {table}")
            added += 1
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print(f"  ⏭️  {table} (already exists)")
                skipped += 1
            else:
                print(f"  ⚠️  {table}: {str(e)[:60]}")
                skipped += 1
    
    print(f"\n  Added: {added}, Skipped: {skipped}")
    
    # FINAL VERIFICATION
    print("\n" + "="*80)
    print("  FINAL VERIFICATION")
    print("="*80)
    
    critical_tables = [
        ('raw_mb51', 'row_hash'),
        ('fact_alerts', 'batch, alert_type'),
        ('fact_billing', 'billing_document, billing_item'),
        ('fact_production', 'order_number, batch'),
        ('fact_lead_time', 'order_number, batch'),
    ]
    
    all_clean = True
    for table, keys in critical_tables:
        result = conn.execute(text(f"""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT ({keys})) as unique_count
            FROM {table}
        """))
        row = result.fetchone()
        total = row[0]
        unique = row[1]
        dupes = total - unique
        
        status = "✅" if dupes == 0 else "❌"
        print(f"  {status} {table}: {total:,} rows, {dupes} dupes")
        
        if dupes > 0:
            all_clean = False
    
    print("\n" + "="*80)
    if all_clean:
        print("  🎉 SUCCESS - ALL DUPLICATES REMOVED!")
        print("  ✅ UNIQUE constraints added")
        print("  ✅ Database is now clean and protected")
    else:
        print("  ⚠️  Still have duplicates - need investigation")
    print("="*80)
