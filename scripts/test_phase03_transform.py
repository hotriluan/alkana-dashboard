"""
Test Phase 3: Transform MB51 with aggregation on local database
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.etl.transform import Transformer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

print("=" * 80)
print("PHASE 3 TEST: Transform MB51 with Aggregation (LOCAL)")
print("=" * 80)
print()

# Step 1: Check raw data
print("1️⃣ Checking raw_mb51 data...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM raw_mb51"))
    raw_count = result.scalar()
    print(f"   Raw MB51 transactions: {raw_count:,}")
    
    if raw_count == 0:
        print("   ⚠️  No raw data - cannot test transform")
        exit(1)
print()

# Step 2: Backup current state
print("2️⃣ Backing up current fact_inventory state...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM fact_inventory"))
    before_count = result.scalar()
    print(f"   Current rows: {before_count:,}")
print()

# Step 3: Run transform_mb51()
print("3️⃣ Running transform_mb51() with aggregation...")
print("-" * 80)
try:
    session = Session()
    transform = Transformer(session)
    transform.transform_mb51()
    session.close()
    print("-" * 80)
    print("   ✅ Transform completed successfully")
except Exception as e:
    print("-" * 80)
    print(f"   ❌ Transform failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
print()

# Step 4: Validate results
print("4️⃣ Validating results...")
with engine.connect() as conn:
    # Check total rows
    result = conn.execute(text("SELECT COUNT(*) FROM fact_inventory"))
    after_count = result.scalar()
    print(f"   ✅ Total rows: {after_count:,}")
    
    # Check for duplicates (should be 0 due to UNIQUE constraint)
    result = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code, posting_date)) as dupes
        FROM fact_inventory
    """))
    dupes = result.scalar()
    
    if dupes > 0:
        print(f"   ❌ FAIL: Found {dupes:,} duplicates!")
    else:
        print(f"   ✅ No duplicates (UNIQUE constraint working)")
    
    # Check total inventory weight
    result = conn.execute(text("SELECT COALESCE(SUM(qty_kg), 0) FROM fact_inventory"))
    total_kg = result.scalar()
    print(f"   ✅ Total inventory weight: {total_kg:,.2f} kg")
    
    # Check unique combinations
    result = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT material_code) as materials,
            COUNT(DISTINCT plant_code) as plants,
            COUNT(DISTINCT posting_date) as dates
        FROM fact_inventory
    """))
    row = result.fetchone()
    print(f"   ✅ Unique materials: {row[0]:,}")
    print(f"   ✅ Unique plants: {row[1]:,}")
    print(f"   ✅ Unique dates: {row[2]:,}")
    
    # Check view_inventory_current
    result = conn.execute(text("SELECT COUNT(*) FROM view_inventory_current"))
    view_count = result.scalar()
    print(f"   ✅ view_inventory_current rows: {view_count:,}")
    
    # Test UNIQUE constraint enforcement
    print()
    print("5️⃣ Testing UNIQUE constraint enforcement...")
    
    # Get a sample record to try duplicating
    result = conn.execute(text("""
        SELECT material_code, plant_code, posting_date 
        FROM fact_inventory 
        LIMIT 1
    """))
    sample = result.fetchone()
    
    if sample:
        try:
            # Try to insert duplicate (should fail)
            conn.execute(text("""
                INSERT INTO fact_inventory (material_code, plant_code, posting_date, mvt_type, qty)
                VALUES (:mat, :plant, :date, 999, 100)
            """), {'mat': sample[0], 'plant': sample[1], 'date': sample[2]})
            conn.commit()
            print(f"   ❌ FAIL: UNIQUE constraint did not block duplicate insert!")
        except Exception as e:
            if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                print(f"   ✅ UNIQUE constraint correctly blocked duplicate insert")
            else:
                print(f"   ⚠️  Unexpected error: {e}")
    
print()
print("=" * 80)

if dupes == 0 and after_count > 0:
    print("✅ PHASE 3 TEST PASSED - Transform working correctly!")
else:
    print("❌ PHASE 3 TEST FAILED - Issues detected")

print("=" * 80)
