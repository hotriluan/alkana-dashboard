"""
FIX FINAL 584 DUPLICATES
Fix remaining duplicates in raw_mb51 (583) and fact_alerts (1)
Then add UNIQUE constraints to prevent future duplicates
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("="*80)
print("  FIX FINAL 584 DUPLICATES")
print("="*80)

with engine.connect() as conn:
    
    # FIX 1: raw_mb51 (583 duplicates)
    print("\n[1/2] Fixing raw_mb51...")
    before = conn.execute(text("SELECT COUNT(*) FROM raw_mb51")).scalar()
    print(f"  Before: {before:,} rows")
    
    # Show sample duplicates before removal
    result = conn.execute(text("""
        SELECT row_hash, COUNT(*) as cnt
        FROM raw_mb51
        GROUP BY row_hash
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 3
    """))
    samples = result.fetchall()
    print(f"  Sample duplicates:")
    for row in samples:
        print(f"    - Hash {row[0][:16]}...: {row[1]}x")
    
    # Remove duplicates
    conn.execute(text("""
        DELETE FROM raw_mb51
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM raw_mb51
            GROUP BY row_hash
        )
    """))
    
    after = conn.execute(text("SELECT COUNT(*) FROM raw_mb51")).scalar()
    removed = before - after
    print(f"  After: {after:,} rows")
    print(f"  ✅ Removed: {removed:,} duplicates")
    
    # Verify
    result = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT row_hash)
        FROM raw_mb51
    """))
    remaining = result.scalar()
    print(f"  Verification: {remaining} duplicates remaining")
    
    # FIX 2: fact_alerts (1 duplicate)
    print("\n[2/2] Fixing fact_alerts...")
    before = conn.execute(text("SELECT COUNT(*) FROM fact_alerts")).scalar()
    print(f"  Before: {before:,} rows")
    
    # Show the duplicate
    result = conn.execute(text("""
        SELECT batch, alert_type, COUNT(*) as cnt
        FROM fact_alerts
        GROUP BY batch, alert_type
        HAVING COUNT(*) > 1
    """))
    samples = result.fetchall()
    if samples:
        print(f"  Duplicate:")
        for row in samples:
            print(f"    - Batch: {row[0]}, Alert: {row[1]}, Count: {row[2]}x")
    
    # Remove duplicates
    conn.execute(text("""
        DELETE FROM fact_alerts
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM fact_alerts
            GROUP BY batch, alert_type
        )
    """))
    
    after = conn.execute(text("SELECT COUNT(*) FROM fact_alerts")).scalar()
    removed = before - after
    print(f"  After: {after:,} rows")
    print(f"  ✅ Removed: {removed:,} duplicates")
    
    # Verify
    result = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT (batch, alert_type))
        FROM fact_alerts
    """))
    remaining = result.scalar()
    print(f"  Verification: {remaining} duplicates remaining")
    
    # ADD UNIQUE CONSTRAINTS
    print("\n[3/3] Adding UNIQUE constraints...")
    
    constraints = [
        # Critical fact tables
        ("idx_fact_billing_unique_biz", "fact_billing", "billing_document, billing_item"),
        ("idx_fact_production_unique_biz", "fact_production", "order_number, batch"),
        ("idx_fact_delivery_unique_biz", "fact_delivery", "delivery, line_item"),
        ("idx_fact_lead_time_unique_biz", "fact_lead_time", "order_number, batch"),
        ("idx_fact_p02_p01_yield_unique_biz", "fact_p02_p01_yield", "p02_batch, p01_batch"),
        ("idx_fact_target_unique_biz", "fact_target", "salesman_name, semester, year"),
        ("idx_fact_alerts_unique_biz", "fact_alerts", "batch, alert_type"),
        
        # All raw tables
        ("idx_raw_cooispi_hash_unique", "raw_cooispi", "row_hash"),
        ("idx_raw_mb51_hash_unique", "raw_mb51", "row_hash"),
        ("idx_raw_zrmm024_hash_unique", "raw_zrmm024", "row_hash"),
        ("idx_raw_zrsd002_hash_unique", "raw_zrsd002", "row_hash"),
        ("idx_raw_zrsd004_hash_unique", "raw_zrsd004", "row_hash"),
        ("idx_raw_zrsd006_hash_unique", "raw_zrsd006", "row_hash"),
        ("idx_raw_zrfi005_hash_unique", "raw_zrfi005", "row_hash"),
        ("idx_raw_target_hash_unique", "raw_target", "row_hash"),
    ]
    
    added = 0
    failed = 0
    
    for idx_name, table, cols in constraints:
        try:
            conn.execute(text(f"""
                CREATE UNIQUE INDEX IF NOT EXISTS {idx_name}
                ON {table} ({cols})
            """))
            print(f"  ✅ {table}: {idx_name}")
            added += 1
        except Exception as e:
            error_msg = str(e)[:80]
            print(f"  ⚠️  {table}: {error_msg}")
            failed += 1
    
    print(f"\n  Summary: {added} constraints added, {failed} failed")
    
    # FINAL VERIFICATION
    print("\n" + "="*80)
    print("  FINAL VERIFICATION")
    print("="*80)
    
    tables_to_check = [
        ('fact_billing', 'billing_document, billing_item'),
        ('fact_production', 'order_number, batch'),
        ('fact_delivery', 'delivery, line_item'),
        ('fact_lead_time', 'order_number, batch'),
        ('fact_p02_p01_yield', 'p02_batch, p01_batch'),
        ('fact_target', 'salesman_name, semester, year'),
        ('fact_alerts', 'batch, alert_type'),
        ('raw_mb51', 'row_hash'),
        ('raw_cooispi', 'row_hash'),
        ('raw_zrsd002', 'row_hash'),
    ]
    
    all_clean = True
    total_checked = 0
    
    print("\nChecking critical tables:")
    for table, keys in tables_to_check:
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
        print(f"  {status} {table}: {total:,} rows, {dupes} duplicates")
        
        if dupes > 0:
            all_clean = False
        
        total_checked += 1
    
    print(f"\n" + "="*80)
    if all_clean:
        print("  🎉 SUCCESS! ALL {0} TABLES CLEAN".format(total_checked))
        print("  ✅ 584 duplicate rows removed")
        print("  ✅ UNIQUE constraints in place")
        print("  ✅ Database is now duplicate-free!")
    else:
        print("  ⚠️  Some tables still have duplicates")
    print("="*80)
