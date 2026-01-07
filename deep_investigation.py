"""
Deep Investigation - 2x Data Duplication

Skills: backend-development, databases
CLAUDE.md: Real Implementation - Find actual duplication source

After full ETL run, still seeing 2x duplication:
- Total AR: 90.6B (should be ~45B)
- Inventory: 698K kg (should be ~350K kg)
- Yield Input: 798K (should be ~400K)
"""
import sys
sys.path.insert(0, '.')

from src.db.connection import engine
from sqlalchemy import text

print("=" * 80)
print("DEEP INVESTIGATION - 2X DUPLICATION")
print("=" * 80)

# Step 1: Check if raw data has duplicates
print("\n[STEP 1] CHECK RAW DATA FOR DUPLICATES")
print("-" * 80)

# Check raw_zrfi005 (AR data)
try:
    total_raw = engine.connect().execute(text("""
        SELECT COUNT(*) FROM raw_zrfi005
    """)).fetchone()[0]
    
    duplicates = engine.connect().execute(text("""
        SELECT customer_code, COUNT(*) as count
        FROM raw_zrfi005
        GROUP BY customer_code
        HAVING COUNT(*) > 1
        LIMIT 5
    """)).fetchall()
    
    print(f"raw_zrfi005 total rows: {total_raw}")
    
    if duplicates:
        print("❌ DUPLICATES IN RAW DATA!")
        for d in duplicates:
            print(f"  Customer {d[0]}: {d[1]} records")
    else:
        print("✅ No duplicates in raw AR data")
        
except Exception as e:
    print(f"Error: {e}")

# Check raw_mb51 (Inventory data)
try:
    total_raw = engine.connect().execute(text("""
        SELECT COUNT(*) FROM raw_mb51
    """)).fetchone()[0]
    
    duplicates = engine.connect().execute(text("""
        SELECT material, plant, COUNT(*) as count
        FROM raw_mb51
        WHERE mvt_type IN ('101', '102', '261', '262')
        GROUP BY material, plant
        HAVING COUNT(*) > 1
        LIMIT 5
    """)).fetchall()
    
    print(f"\nraw_mb51 total rows: {total_raw}")
    
    if duplicates:
        print("❌ DUPLICATES IN RAW DATA!")
        for d in duplicates:
            print(f"  Material {d[0]} at Plant {d[1]}: {d[2]} records")
    else:
        print("✅ No duplicates in raw inventory data")
        
except Exception as e:
    print(f"Error: {e}")

# Step 2: Check transform logic - are we inserting duplicates?
print("\n[STEP 2] CHECK FACT TABLE DUPLICATES")
print("-" * 80)

# Check fact_ar_aging for duplicates
try:
    duplicates = engine.connect().execute(text("""
        SELECT customer_code, COUNT(*) as count
        FROM fact_ar_aging
        GROUP BY customer_code
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """)).fetchall()
    
    if duplicates:
        print("❌ DUPLICATES IN fact_ar_aging!")
        print("Customers with multiple records:")
        for d in duplicates:
            print(f"  {d[0]}: {d[1]} records")
            
        # Check one specific customer
        sample = duplicates[0][0]
        details = engine.connect().execute(text(f"""
            SELECT id, customer_code, total_ar, source_row
            FROM fact_ar_aging
            WHERE customer_code = '{sample}'
        """)).fetchall()
        
        print(f"\nDetailed records for customer {sample}:")
        for r in details:
            print(f"  ID {r[0]}: AR={r[2]:,.0f}, source_row={r[3]}")
    else:
        print("✅ No duplicates in fact_ar_aging")
        
except Exception as e:
    print(f"Error: {e}")

# Check fact_inventory for duplicates
try:
    duplicates = engine.connect().execute(text("""
        SELECT material, plant, COUNT(*) as count
        FROM fact_inventory
        GROUP BY material, plant
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """)).fetchall()
    
    if duplicates:
        print("\n❌ DUPLICATES IN fact_inventory!")
        print("Material+Plant with multiple records:")
        for d in duplicates:
            print(f"  {d[0]} at Plant {d[1]}: {d[2]} records")
            
        # Check one specific material
        sample_mat = duplicates[0][0]
        sample_plant = duplicates[0][1]
        details = engine.connect().execute(text(f"""
            SELECT id, material, plant, quantity_kg, mvt_type
            FROM fact_inventory
            WHERE material = '{sample_mat}' AND plant = {sample_plant}
        """)).fetchall()
        
        print(f"\nDetailed records for {sample_mat} at Plant {sample_plant}:")
        for r in details:
            print(f"  ID {r[0]}: {r[3]:,.2f} kg, mvt_type={r[4]}")
    else:
        print("✅ No duplicates in fact_inventory")
        
except Exception as e:
    print(f"Error: {e}")

# Step 3: Check transform logic - multiple inserts?
print("\n[STEP 3] ANALYZING TRANSFORM LOGIC")
print("-" * 80)

print("""
Checking transform_zrfi005() and transform_mb51():
1. Do they insert each raw row once or multiple times?
2. Are there any loops that cause duplicate inserts?
3. Is there any JOIN that multiplies rows?
""")

# Check if transform is being called multiple times
print("\nReview src/etl/transform.py transform_all():")
print("Does it call each transform function once or multiple times?")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

print("""
POSSIBLE CAUSES:
1. Raw data has duplicates (loaded same file twice)
2. Transform logic inserts each row twice
3. Transform function called twice in transform_all()
4. JOIN in transform multiplies rows

NEXT STEPS:
1. Check raw data load - did we load files twice?
2. Review transform_zrfi005() for duplicate inserts
3. Review transform_mb51() for duplicate inserts
4. Check for JOINs that multiply rows
""")

print("=" * 80)
