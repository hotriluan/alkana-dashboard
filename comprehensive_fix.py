"""
COMPREHENSIVE DATA FIX - Executive Dashboard
Skills: ETL, databases, data-quality, problem-solving
Claude Kit: DRY, KISS, Systematic approach

Fixes:
1. Remove duplicate rows in raw_zrsd002
2. Fix customer name column mapping
3. Re-transform clean data
4. Validate results
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alkana_db")
engine = create_engine(DATABASE_URL)

print("="*80)
print("COMPREHENSIVE DATA FIX - EXECUTIVE DASHBOARD")
print("="*80)

# ============================================================================
# STEP 1: Clean Duplicate Data in raw_zrsd002
# ============================================================================
print("\n" + "="*80)
print("STEP 1: REMOVING DUPLICATE DATA")
print("="*80)

with engine.connect() as conn:
    # Check current state
    result = conn.execute(text("SELECT COUNT(*) FROM raw_zrsd002"))
    before_count = result.fetchone()[0]
    print(f"\nBefore: {before_count} rows in raw_zrsd002")
    
    # Find duplicates based on billing document + item
    result2 = conn.execute(text("""
        WITH duplicates AS (
            SELECT 
                raw_data->>'Billing Document' as doc,
                raw_data->>'Billing Item' as item,
                COUNT(*) as cnt
            FROM raw_zrsd002
            GROUP BY raw_data->>'Billing Document', raw_data->>'Billing Item'
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(*), SUM(cnt - 1) as duplicate_rows
        FROM duplicates
    """))
    dup_info = result2.fetchone()
    if dup_info and dup_info[1]:
        print(f"Found: {dup_info[0]} unique rows with duplicates")
        print(f"Total duplicate rows to remove: {dup_info[1]}")
    else:
        print("No duplicates found (unusual - check row_hash)")
    
    # Delete duplicates (keep first occurrence based on billing doc + item)
    print("\nDeleting duplicates...")
    result3 = conn.execute(text("""
        DELETE FROM raw_zrsd002
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM raw_zrsd002
            GROUP BY raw_data->>'Billing Document', raw_data->>'Billing Item'
        )
    """))
    conn.commit()
    
    deleted = result3.rowcount
    print(f"✓ Deleted {deleted} duplicate rows")
    
    # Verify
    result4 = conn.execute(text("SELECT COUNT(*) FROM raw_zrsd002"))
    after_count = result4.fetchone()[0]
    print(f"After: {after_count} rows in raw_zrsd002")
    print(f"Expected: ~21,072 rows")
    
    if after_count == 21072:
        print("✓ SUCCESS: Row count matches Excel!")
    elif abs(after_count - 21072) < 100:
        print("⚠ CLOSE: Row count within tolerance")
    else:
        print(f"❌ WARNING: Row count mismatch ({after_count} vs 21,072)")

# ============================================================================
# STEP 2: Update raw_zrsd002 with correct customer names
# ============================================================================
print("\n" + "="*80)
print("STEP 2: FIX CUSTOMER NAME MAPPING")
print("="*80)

print("\nUpdating customer_name from 'Name of Bill to'...")
with engine.connect() as conn:
    # Update customer_name from raw_data JSONB
    result = conn.execute(text("""
        UPDATE raw_zrsd002
        SET customer_name = raw_data->>'Name of Bill to'
        WHERE raw_data->>'Name of Bill to' IS NOT NULL
    """))
    conn.commit()
    
    updated = result.rowcount
    print(f"✓ Updated {updated} rows with customer names")
    
    # Verify
    result2 = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT customer_name) as unique_customers,
            COUNT(CASE WHEN customer_name IS NULL THEN 1 END) as null_count
        FROM raw_zrsd002
    """))
    row = result2.fetchone()
    print(f"\nVerification:")
    print(f"  Total rows: {row[0]}")
    print(f"  Unique customers: {row[1]}")
    print(f"  NULL customers: {row[2]}")
    
    if row[1] > 200:
        print(f"✓ SUCCESS: {row[1]} customers found (expected ~210)")
    else:
        print(f"❌ WARNING: Only {row[1]} customers (expected ~210)")

# ============================================================================
# STEP 3: Clear and Re-transform fact_billing
# ============================================================================
print("\n" + "="*80)
print("STEP 3: RE-TRANSFORM DATA")
print("="*80)

print("\nClearing fact_billing...")
with engine.connect() as conn:
    result = conn.execute(text("DELETE FROM fact_billing"))
    conn.commit()
    deleted = result.rowcount
    print(f"✓ Deleted {deleted} old records")

print("\nRe-transforming raw_zrsd002 → fact_billing...")
print("(This will run the Python transform function)\n")

try:
    from src.etl.transform import Transformer
    from src.db.connection import get_db
    
    db = next(get_db())
    transformer = Transformer(db)
    transformer.transform_zrsd002()
    db.close()
    
    print("\n✓ Transform completed")
except Exception as e:
    print(f"\n❌ Transform error: {e}")
    print("You may need to run manually:")
    print("  python -c \"from src.etl.transform import Transformer; ...\"")

# ============================================================================
# STEP 4: Validate Results
# ============================================================================
print("\n" + "="*80)
print("STEP 4: VALIDATION")
print("="*80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT billing_document) as unique_docs,
            SUM(net_value) as total_revenue,
            COUNT(DISTINCT customer_name) as unique_customers,
            COUNT(CASE WHEN customer_name IS NULL THEN 1 END) as null_customers
        FROM fact_billing
        WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'
    """))
    row = result.fetchone()
    
    print(f"\nfact_billing (2025 data):")
    print(f"  Total Rows: {row[0]:,}")
    print(f"  Unique Documents: {row[1]:,}")
    print(f"  Total Revenue: {row[2]:,.2f}" if row[2] else "  Total Revenue: 0")
    print(f"  Unique Customers: {row[3]:,}")
    print(f"  NULL Customers: {row[4]:,}")
    
    # Expected values
    expected_rows = 21072
    expected_revenue = 278240644750.76
    expected_customers = 210
    
    print(f"\n📊 COMPARISON:")
    print(f"  Rows:      {row[0]:,} vs {expected_rows:,} expected")
    print(f"  Revenue:   {row[2]:,.0f} vs {expected_revenue:,.0f} expected" if row[2] else "  Revenue: 0")
    print(f"  Customers: {row[3]:,} vs {expected_customers:,} expected")
    
    # Validation
    issues = []
    if abs(row[0] - expected_rows) > 100:
        issues.append(f"Row count mismatch: {row[0]} vs {expected_rows}")
    
    if row[2]:
        revenue_diff_pct = abs((float(row[2]) - expected_revenue) / expected_revenue * 100)
        if revenue_diff_pct > 1:
            issues.append(f"Revenue mismatch: {revenue_diff_pct:.1f}%")
    
    if row[3] == 0:
        issues.append("No customers found")
    
    if issues:
        print(f"\n❌ ISSUES REMAINING:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"\n✅ ALL VALIDATIONS PASSED!")
        print(f"   Dashboard should now show correct data:")
        print(f"   - Revenue: ~278B VND")
        print(f"   - Customers: ~210 unique customers")
        print(f"   - No duplicates")

print("\n" + "="*80)
print("FIX COMPLETED")
print("="*80)
print("\nNext step: Refresh your browser to see updated dashboard")
