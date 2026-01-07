"""
FIX REMAINING DUPLICATES

Automatically fix duplicates in:
1. fact_p02_p01_yield (2,214 duplicates)
2. fact_target (36 duplicates)
3. raw_mb51 (583 duplicates)

Then add UNIQUE constraints to prevent future duplicates.
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

print("="*80)
print("  FIX REMAINING DUPLICATES - 3 TABLES")
print("="*80)

with engine.connect() as conn:
    
    # ========================================================================
    # FIX 1: fact_p02_p01_yield (2,214 duplicates)
    # ========================================================================
    print("\n[FIX 1] Removing duplicates from fact_p02_p01_yield...")
    
    # Check before
    result = conn.execute(text("SELECT COUNT(*) FROM fact_p02_p01_yield"))
    before_count = result.scalar()
    print(f"  Before: {before_count:,} rows")
    
    # Remove duplicates - keep earliest record (MIN id)
    conn.execute(text("""
        DELETE FROM fact_p02_p01_yield
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM fact_p02_p01_yield
            GROUP BY p02_batch, p01_batch
        )
    """))
    conn.commit()
    
    # Check after
    result = conn.execute(text("SELECT COUNT(*) FROM fact_p02_p01_yield"))
    after_count = result.scalar()
    removed = before_count - after_count
    print(f"  After: {after_count:,} rows")
    print(f"  Removed: {removed:,} duplicates")
    
    # Verify no duplicates remain
    result = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT (p02_batch, p01_batch))
        FROM fact_p02_p01_yield
    """))
    remaining_dupes = result.scalar()
    print(f"  Verification: {remaining_dupes} duplicates remaining")
    
    if remaining_dupes == 0:
        print("  ✅ SUCCESS - All duplicates removed")
    else:
        print(f"  ⚠️  WARNING - Still has {remaining_dupes} duplicates")
    
    # ========================================================================
    # FIX 2: fact_target (36 duplicates)
    # ========================================================================
    print("\n[FIX 2] Removing duplicates from fact_target...")
    
    # Check before
    result = conn.execute(text("SELECT COUNT(*) FROM fact_target"))
    before_count = result.scalar()
    print(f"  Before: {before_count:,} rows")
    
    # Remove duplicates
    conn.execute(text("""
        DELETE FROM fact_target
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM fact_target
            GROUP BY salesman_name, semester, year
        )
    """))
    conn.commit()
    
    # Check after
    result = conn.execute(text("SELECT COUNT(*) FROM fact_target"))
    after_count = result.scalar()
    removed = before_count - after_count
    print(f"  After: {after_count:,} rows")
    print(f"  Removed: {removed:,} duplicates")
    
    # Verify
    result = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT (salesman_name, semester, year))
        FROM fact_target
    """))
    remaining_dupes = result.scalar()
    print(f"  Verification: {remaining_dupes} duplicates remaining")
    
    if remaining_dupes == 0:
        print("  ✅ SUCCESS - All duplicates removed")
    else:
        print(f"  ⚠️  WARNING - Still has {remaining_dupes} duplicates")
    
    # ========================================================================
    # FIX 3: raw_mb51 (583 duplicates)
    # ========================================================================
    print("\n[FIX 3] Removing duplicates from raw_mb51...")
    
    # Check before
    result = conn.execute(text("SELECT COUNT(*) FROM raw_mb51"))
    before_count = result.scalar()
    print(f"  Before: {before_count:,} rows")
    
    # Remove duplicates based on row_hash
    conn.execute(text("""
        DELETE FROM raw_mb51
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM raw_mb51
            GROUP BY row_hash
        )
    """))
    conn.commit()
    
    # Check after
    result = conn.execute(text("SELECT COUNT(*) FROM raw_mb51"))
    after_count = result.scalar()
    removed = before_count - after_count
    print(f"  After: {after_count:,} rows")
    print(f"  Removed: {removed:,} duplicates")
    
    # Verify
    result = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT row_hash)
        FROM raw_mb51
    """))
    remaining_dupes = result.scalar()
    print(f"  Verification: {remaining_dupes} duplicates remaining")
    
    if remaining_dupes == 0:
        print("  ✅ SUCCESS - All duplicates removed")
    else:
        print(f"  ⚠️  WARNING - Still has {remaining_dupes} duplicates")
    
    # ========================================================================
    # ADD UNIQUE CONSTRAINTS
    # ========================================================================
    print("\n[STEP 4] Adding UNIQUE constraints to prevent future duplicates...")
    
    constraints = [
        # Fact tables
        ("idx_fact_billing_unique", "fact_billing", "billing_document, billing_item"),
        ("idx_fact_production_unique", "fact_production", "order_number, batch"),
        ("idx_fact_delivery_unique", "fact_delivery", "delivery, line_item"),
        ("idx_fact_lead_time_unique", "fact_lead_time", "order_number, batch"),
        ("idx_fact_p02_p01_yield_unique", "fact_p02_p01_yield", "p02_batch, p01_batch"),
        ("idx_fact_target_unique", "fact_target", "salesman_name, semester, year"),
        
        # Raw tables (using row_hash)
        ("idx_raw_cooispi_hash", "raw_cooispi", "row_hash"),
        ("idx_raw_mb51_hash", "raw_mb51", "row_hash"),
        ("idx_raw_zrmm024_hash", "raw_zrmm024", "row_hash"),
        ("idx_raw_zrsd002_hash", "raw_zrsd002", "row_hash"),
        ("idx_raw_zrsd004_hash", "raw_zrsd004", "row_hash"),
        ("idx_raw_zrsd006_hash", "raw_zrsd006", "row_hash"),
        ("idx_raw_zrfi005_hash", "raw_zrfi005", "row_hash"),
        ("idx_raw_target_hash", "raw_target", "row_hash"),
    ]
    
    added_count = 0
    skipped_count = 0
    
    for index_name, table_name, columns in constraints:
        try:
            conn.execute(text(f"""
                CREATE UNIQUE INDEX IF NOT EXISTS {index_name}
                ON {table_name} ({columns})
            """))
            conn.commit()
            print(f"  ✅ Added: {index_name} on {table_name}")
            added_count += 1
        except Exception as e:
            print(f"  ⚠️  Skipped {index_name}: {str(e)[:80]}")
            skipped_count += 1
    
    print(f"\n  Summary: {added_count} constraints added, {skipped_count} skipped")
    
    # ========================================================================
    # FINAL VALIDATION
    # ========================================================================
    print("\n" + "="*80)
    print("  FINAL VALIDATION")
    print("="*80)
    
    # Check all fact tables
    fact_tables = [
        ('fact_billing', 'billing_document, billing_item'),
        ('fact_production', 'order_number, batch'),
        ('fact_delivery', 'delivery, line_item'),
        ('fact_lead_time', 'order_number, batch'),
        ('fact_p02_p01_yield', 'p02_batch, p01_batch'),
        ('fact_target', 'salesman_name, semester, year'),
    ]
    
    print("\nFact Tables:")
    all_clean = True
    for table, keys in fact_tables:
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
    
    # Check raw tables
    raw_tables = [
        'raw_cooispi', 'raw_mb51', 'raw_zrmm024',
        'raw_zrsd002', 'raw_zrsd004', 'raw_zrsd006',
        'raw_zrfi005', 'raw_target'
    ]
    
    print("\nRaw Tables:")
    for table in raw_tables:
        result = conn.execute(text(f"""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT row_hash) as unique_count
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
    
    print("\n" + "="*80)
    if all_clean:
        print("  🎉 SUCCESS - ALL TABLES CLEAN, NO DUPLICATES!")
        print("  UNIQUE constraints in place to prevent future duplicates")
    else:
        print("  ⚠️  WARNING - Some tables still have duplicates")
    print("="*80)
