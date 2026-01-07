"""
COMPREHENSIVE FIX - All Issues Found in Audit

Issues to fix:
1. fact_billing: 21,072 duplicates
2. fact_lead_time: 1,849 duplicates  
3. raw_zrsd006: Empty (needs re-load)
4. AR Collection empty display (API issue)
5. zrsd004 header detection
6. Date filters missing in many APIs

Step-by-step fix:
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import sys

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

print("="*80)
print("  COMPREHENSIVE FIX - ALL ISSUES")
print("="*80)

# ========== FIX 1: Remove Duplicates from fact_billing ==========
print("\n[FIX 1] Removing duplicates from fact_billing...")
session = Session()
try:
    before = session.execute(text("SELECT COUNT(*) FROM fact_billing")).scalar()
    print(f"  Before: {before:,} rows")
    
    # Delete duplicates, keep MIN(id)
    session.execute(text("""
        DELETE FROM fact_billing
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM fact_billing
            GROUP BY billing_document, billing_item
        )
    """))
    session.commit()
    
    after = session.execute(text("SELECT COUNT(*) FROM fact_billing")).scalar()
    print(f"  After: {after:,} rows")
    print(f"  Removed: {before - after:,} duplicates")
    
    # Also need to fix customer_name (half are NULL)
    null_count = session.execute(text("""
        SELECT COUNT(*) FROM fact_billing WHERE customer_name IS NULL
    """)).scalar()
    
    if null_count > 0:
        print(f"\n  Fixing {null_count:,} NULL customer names...")
        session.execute(text("""
            UPDATE fact_billing
            SET customer_name = raw_zrsd002.raw_data->>'Name of Bill to'
            FROM raw_zrsd002
            WHERE fact_billing.billing_document = raw_zrsd002.raw_data->>'Billing Document'
              AND fact_billing.billing_item::text = raw_zrsd002.raw_data->>'Billing Item'
              AND fact_billing.customer_name IS NULL
        """))
        session.commit()
        
        after_fix = session.execute(text("""
            SELECT COUNT(*) FROM fact_billing WHERE customer_name IS NULL
        """)).scalar()
        print(f"  Fixed: {null_count - after_fix:,} customer names")
    
except Exception as e:
    session.rollback()
    print(f"  ERROR: {e}")
finally:
    session.close()

# ========== FIX 2: Remove Duplicates from fact_lead_time ==========
print("\n[FIX 2] Removing duplicates from fact_lead_time...")
session = Session()
try:
    before = session.execute(text("SELECT COUNT(*) FROM fact_lead_time")).scalar()
    print(f"  Before: {before:,} rows")
    
    session.execute(text("""
        DELETE FROM fact_lead_time
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM fact_lead_time
            GROUP BY order_number, COALESCE(batch, '')
        )
    """))
    session.commit()
    
    after = session.execute(text("SELECT COUNT(*) FROM fact_lead_time")).scalar()
    print(f"  After: {after:,} rows")
    print(f"  Removed: {before - after:,} duplicates")
    
except Exception as e:
    session.rollback()
    print(f"  ERROR: {e}")
finally:
    session.close()

# ========== FIX 3: Re-load raw_zrsd006 ==========
print("\n[FIX 3] Re-loading raw_zrsd006...")
sys.path.insert(0, 'src')

try:
    from src.etl.loaders import Zrsd006Loader
    
    session = Session()
    loader = Zrsd006Loader(session, mode='insert')
    result = loader.load()
    session.close()
    
    print(f"  Loaded: {result['loaded']:,} rows")
    if result['errors'] > 0:
        print(f"  Errors: {result['errors']:,}")
        
except Exception as e:
    print(f"  ERROR: {e}")

# ========== VALIDATION ==========
print("\n" + "="*80)
print("  VALIDATION")
print("="*80)

session = Session()
try:
    # Check fact_billing
    result = session.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT billing_document || '-' || billing_item) as unique,
            SUM(net_value)/1000000000 as revenue_b,
            COUNT(CASE WHEN customer_name IS NULL THEN 1 END) as null_customers
        FROM fact_billing
    """)).fetchone()
    
    print(f"\nfact_billing:")
    print(f"  Rows: {result[0]:,} ({'OK' if result[0] == result[1] else 'DUPLICATES!'})")
    print(f"  Revenue: {result[2]:.2f}B VND")
    print(f"  NULL Customers: {result[3]:,} ({'OK' if result[3] == 0 else 'ISSUE'})")
    
    # Check fact_lead_time
    result = session.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT order_number || '-' || COALESCE(batch, '')) as unique
        FROM fact_lead_time
    """)).fetchone()
    
    print(f"\nfact_lead_time:")
    print(f"  Rows: {result[0]:,} ({'OK' if result[0] == result[1] else 'DUPLICATES!'})")
    
    # Check raw_zrsd006
    count = session.execute(text("SELECT COUNT(*) FROM raw_zrsd006")).scalar()
    print(f"\nraw_zrsd006:")
    print(f"  Rows: {count:,} ({'OK' if count > 0 else 'STILL EMPTY!'})")
    
finally:
    session.close()

print("\n" + "="*80)
print("  FIX COMPLETED!")
print("="*80)
print("\nRemaining tasks:")
print("  - Fix zrsd004 header detection")
print("  - Add date filters to missing APIs")
print("  - Investigate AR Collection display issue")
