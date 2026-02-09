"""
Phase 3 Validation: Test aggregated transform_mb51()
"""
from src.etl.transform import ETLTransform
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("PHASE 3 VALIDATION: Test Aggregated transform_mb51()")
print("=" * 80)
print()

# Step 1: Check raw_mb51 data
print("1. Checking raw_mb51 data...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM raw_mb51"))
    raw_count = result.scalar()
    print(f"   Raw MB51 transactions: {raw_count:,}")
print()

# Step 2: Run transform_mb51()
print("2. Running transform_mb51() with aggregation...")
try:
    transform = ETLTransform()
    transform.transform_mb51()
    print("   ✓ Transform completed successfully")
except Exception as e:
    print(f"   ❌ Transform failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
print()

# Step 3: Validate results
print("3. Validating results...")
with engine.connect() as conn:
    # Check total rows
    result = conn.execute(text("SELECT COUNT(*) FROM fact_inventory"))
    fact_count = result.scalar()
    print(f"   fact_inventory rows: {fact_count:,}")
    
    # Check for duplicates (should be 0)
    result = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code, posting_date)) as dupes
        FROM fact_inventory
    """))
    dupes = result.scalar()
    print(f"   Duplicates: {dupes:,}")
    
    if dupes > 0:
        print("   ❌ FAIL: Found duplicates after aggregation!")
    else:
        print("   ✓ PASS: No duplicates (UNIQUE constraint satisfied)")
    
    # Check total inventory weight
    result = conn.execute(text("SELECT SUM(qty_kg) FROM fact_inventory"))
    total_kg = result.scalar()
    print(f"   Total inventory weight: {total_kg:,.2f} kg")
    
    # Check unique materials/plants/dates
    result = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT material_code) as materials,
            COUNT(DISTINCT plant_code) as plants,
            COUNT(DISTINCT posting_date) as dates
        FROM fact_inventory
    """))
    row = result.fetchone()
    print(f"   Unique materials: {row[0]:,}")
    print(f"   Unique plants: {row[1]:,}")
    print(f"   Unique dates: {row[2]:,}")
    
print()
print("=" * 80)
print("✓ VALIDATION COMPLETE")
print("=" * 80)
