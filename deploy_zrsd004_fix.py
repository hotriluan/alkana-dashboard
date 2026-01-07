"""
Deploy ZRSD004 Fix to Production
1. Truncate tables
2. Re-load data with fixed loader
"""
from sqlalchemy import create_engine, text
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("="*80)
print("  DEPLOY ZRSD004 FIX TO PRODUCTION")
print("="*80)

with engine.connect() as conn:
    # Step 1: Check current state
    print("\n[STEP 1] Current State")
    print("-" * 80)
    
    raw_count = conn.execute(text("SELECT COUNT(*) FROM raw_zrsd004")).scalar()
    fact_count = conn.execute(text("SELECT COUNT(*) FROM fact_delivery")).scalar()
    
    print(f"  raw_zrsd004: {raw_count:,} rows")
    print(f"  fact_delivery: {fact_count:,} rows")
    
    # Check for NULL data
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN raw_data->>'Delivery' IS NOT NULL THEN 1 END) as has_delivery
        FROM raw_zrsd004
    """))
    row = result.fetchone()
    
    if row[0] > 0:
        null_pct = (1 - row[1]/row[0]) * 100
        print(f"  NULL Deliveries: {null_pct:.1f}%")
        
        if null_pct > 50:
            print(f"  ⚠️  High NULL percentage - data is corrupted")
        else:
            print(f"  ✓ Data looks OK")
    
    # Step 2: Backup check
    print("\n[STEP 2] Backup Verification")
    print("-" * 80)
    print("  ⚠️  IMPORTANT: Ensure database backup exists before proceeding")
    print("  Current tables will be TRUNCATED")
    
    response = input("\n  Continue with truncate? (yes/no): ")
    if response.lower() != 'yes':
        print("  ❌ Deployment cancelled")
        exit(0)
    
    # Step 3: Truncate tables
    print("\n[STEP 3] Truncating Tables")
    print("-" * 80)
    
    conn.execute(text("TRUNCATE TABLE fact_delivery CASCADE"))
    print("  ✓ fact_delivery truncated")
    
    conn.execute(text("TRUNCATE TABLE raw_zrsd004 CASCADE"))
    print("  ✓ raw_zrsd004 truncated")
    
    # Verify
    raw_count = conn.execute(text("SELECT COUNT(*) FROM raw_zrsd004")).scalar()
    fact_count = conn.execute(text("SELECT COUNT(*) FROM fact_delivery")).scalar()
    
    print(f"\n  Verification:")
    print(f"    raw_zrsd004: {raw_count} rows (should be 0)")
    print(f"    fact_delivery: {fact_count} rows (should be 0)")
    
    if raw_count == 0 and fact_count == 0:
        print(f"  ✅ Tables truncated successfully")
    else:
        print(f"  ❌ Truncate failed!")
        exit(1)

print("\n[STEP 4] Re-load Data")
print("-" * 80)
print("  Now run the loader with fixed code:")
print("  ")
print("  >>> from src.etl.loaders import Zrsd004Loader")
print("  >>> loader = Zrsd004Loader()")
print("  >>> result = loader.load()")
print("  ")
print("  Expected: 24,856 rows loaded with populated data")

print("\n" + "="*80)
print("  DEPLOYMENT PREPARATION COMPLETE")
print("  Ready to load data with fixed loader")
print("="*80)
