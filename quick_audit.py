"""
Quick Database Audit - Check critical issues only
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("="*80)
print("  QUICK DATABASE AUDIT")
print("="*80)

with engine.connect() as conn:
    
    print("\n[CRITICAL ISSUE 1] fact_billing Duplicates:")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT billing_document || '-' || billing_item) as unique_keys,
            COUNT(*) - COUNT(DISTINCT billing_document || '-' || billing_item) as duplicates
        FROM fact_billing
    """)).fetchone()
    print(f"  Total: {result[0]:,}")
    print(f"  Unique: {result[1]:,}")
    print(f"  Duplicates: {result[2]:,} {'*** ACTION REQUIRED ***' if result[2] > 0 else 'OK'}")
    
    print("\n[CRITICAL ISSUE 2] fact_ar_aging Empty:")
    result = conn.execute(text("SELECT COUNT(*) FROM fact_ar_aging")).fetchone()
    print(f"  Rows: {result[0]:,} {'*** AR Collection will be EMPTY ***' if result[0] == 0 else 'OK'}")
    
    print("\n[CRITICAL ISSUE 3] Raw Tables Empty:")
    tables = ['raw_cooispi', 'raw_mb51', 'raw_zrmm024', 'raw_zrsd002', 'raw_zrsd004', 'raw_zrsd006']
    for table in tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        if count == 0:
            print(f"  {table}: {count:,} *** EMPTY ***")
        else:
            print(f"  {table}: {count:,} OK")
    
    print("\n[CRITICAL ISSUE 4] fact_lead_time Duplicates:")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT order_number || '-' || COALESCE(batch, '')) as unique_keys,
            COUNT(*) - COUNT(DISTINCT order_number || '-' || COALESCE(batch, '')) as duplicates
        FROM fact_lead_time
    """)).fetchone()
    print(f"  Total: {result[0]:,}")
    print(f"  Unique: {result[1]:,}")
    print(f"  Duplicates: {result[2]:,} {'*** ACTION REQUIRED ***' if result[2] > 0 else 'OK'}")
    
    print("\n" + "="*80)
    print("  ACTION ITEMS:")
    print("="*80)
    print("1. Truncate fact_billing and re-transform (has 21K duplicates)")
    print("2. Fix fact_ar_aging empty table (AR Collection broken)")
    print("3. Re-load empty raw tables")
    print("4. Fix zrsd004 header detection")
    print("5. Add date filters to all APIs")
