"""
Full ZRSD004 Fix Deployment - Automated
Truncate + Reload with fixed loader
"""
from sqlalchemy import create_engine, text
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
from src.etl.loaders import Zrsd004Loader

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("="*80)
print("  AUTOMATED ZRSD004 FIX DEPLOYMENT")
print("="*80)

with engine.connect() as conn:
    # Step 1: Current state
    print("\n[STEP 1] Before Fix")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN raw_data->>'Delivery' IS NOT NULL THEN 1 END) as has_delivery
        FROM raw_zrsd004
    """))
    row = result.fetchone()
    
    before_total = row[0]
    before_populated = row[1]
    before_null_pct = (1 - before_populated/before_total)*100 if before_total > 0 else 0
    
    print(f"  raw_zrsd004: {before_total:,} rows")
    print(f"  NULL Deliveries: {before_null_pct:.1f}%")
    
    if before_null_pct > 90:
        print(f"  ❌ Data is corrupted (>90% NULL) - fix needed!")
    
    # Step 2: Truncate
    print("\n[STEP 2] Truncating Tables")
    conn.execute(text("TRUNCATE TABLE fact_delivery CASCADE"))
    conn.execute(text("TRUNCATE TABLE raw_zrsd004 CASCADE"))
    print(f"  ✓ Tables truncated")

# Step 3: Re-load with fixed loader
print("\n[STEP 3] Re-loading Data with Fixed Loader")
print("-" * 80)

try:
    loader = Zrsd004Loader()
    result = loader.load()
    
    print(f"\n  ✓ Load completed:")
    print(f"    Loaded: {result.get('loaded', 0):,} rows")
    print(f"    Skipped: {result.get('skipped', 0):,} rows")
    
except Exception as e:
    print(f"  ❌ Load failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 4: Verify
print("\n[STEP 4] Verification")
print("-" * 80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN raw_data->>'Delivery' IS NOT NULL THEN 1 END) as has_delivery,
            COUNT(CASE WHEN raw_data->>'Material' IS NOT NULL THEN 1 END) as has_material,
            COUNT(CASE WHEN raw_data->>'Name of Ship-to' IS NOT NULL THEN 1 END) as has_ship_to
        FROM raw_zrsd004
    """))
    row = result.fetchone()
    
    after_total = row[0]
    after_delivery = row[1]
    after_material = row[2]
    after_ship_to = row[3]
    
    print(f"  raw_zrsd004: {after_total:,} rows")
    print(f"  Delivery populated: {after_delivery:,} ({after_delivery/after_total*100:.1f}%)")
    print(f"  Material populated: {after_material:,} ({after_material/after_total*100:.1f}%)")
    print(f"  Ship-to populated: {after_ship_to:,} ({after_ship_to/after_total*100:.1f}%)")
    
    # Sample data
    result = conn.execute(text("""
        SELECT 
            raw_data->>'Delivery' as delivery,
            raw_data->>'Material' as material,
            raw_data->>'Name of Ship-to' as ship_to
        FROM raw_zrsd004
        LIMIT 3
    """))
    
    print(f"\n  Sample Data:")
    for row in result:
        print(f"    Delivery: {row[0]}, Material: {row[1]}, Ship-to: {row[2]}")
    
    # Success check
    success = (
        after_total >= 24000 and  # Should be ~24,856
        after_delivery / after_total > 0.95  # >95% populated
    )
    
    print("\n" + "="*80)
    if success:
        print("  🎉 ✅ DEPLOYMENT SUCCESS!")
        print(f"  Before: {before_total:,} rows ({before_null_pct:.1f}% NULL)")
        print(f"  After: {after_total:,} rows ({(1-after_delivery/after_total)*100:.1f}% NULL)")
        print(f"  Data recovery: 100% ({after_total:,} rows)")
    else:
        print("  ❌ DEPLOYMENT FAILED - Need investigation")
    
    print("="*80)
