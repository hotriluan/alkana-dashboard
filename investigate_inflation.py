"""
Investigate Data Inflation Issues
Check for JOIN multiplication and aggregation problems
"""
from src.db.connection import engine
from sqlalchemy import text

print("=" * 80)
print("DATA INFLATION INVESTIGATION")
print("=" * 80)

# Test 1: Check if raw_zrsd006 has duplicate materials
print("\n[TEST 1] Checking raw_zrsd006 for duplicate materials...")
result = engine.connect().execute(text("""
    SELECT material, COUNT(*) as cnt
    FROM raw_zrsd006
    GROUP BY material
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
    LIMIT 10
""")).fetchall()

if result:
    print("⚠️  WARNING: raw_zrsd006 has materials with multiple rows!")
    print("This will cause JOIN multiplication in leadtime queries!\n")
    for row in result:
        print(f"  Material {row[0]}: {row[1]} rows")
    print(f"\nTotal duplicates: {len(result)} materials have >1 row")
else:
    print("✅ No duplicates in raw_zrsd006")

# Test 2: Check if JOIN causes row multiplication
print("\n[TEST 2] Testing JOIN multiplication...")
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as prod_rows,
        (SELECT COUNT(*) FROM raw_zrsd006) as zrsd_rows
    FROM fact_production
""")).fetchone()

print(f"fact_production rows: {result[0]:,}")
print(f"raw_zrsd006 rows: {result[1]:,}")

# Now check what happens with LEFT JOIN
result2 = engine.connect().execute(text("""
    WITH joined AS (
        SELECT fp.*, rz.dist_channel
        FROM fact_production fp
        LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    )
    SELECT COUNT(*) as joined_rows
    FROM joined
""")).fetchone()

print(f"After LEFT JOIN: {result2[0]:,} rows")

if result2[0] > result[0]:
    inflation = ((result2[0] / result[0]) - 1) * 100
    print(f"❌ PROBLEM: JOIN inflates data by {inflation:.1f}%!")
    print("   This means some materials match multiple rows in raw_zrsd006")
else:
    print("✅ No JOIN multiplication detected")

# Test 3: Check view_inventory_current for duplicates
print("\n[TEST 3] Checking view_inventory_current for duplicates...")
result = engine.connect().execute(text("""
    SELECT material_code, plant_code, COUNT(*) as cnt
    FROM view_inventory_current
    GROUP BY material_code, plant_code
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
    LIMIT 10
""")).fetchall()

if result:
    print("❌ PROBLEM: view_inventory_current has duplicates!")
    for row in result:
        print(f"  Material {row[0]} at Plant {row[1]}: {row[2]} rows")
else:
    print("✅ No duplicates in view_inventory_current")

# Test 4: Check fact_inventory aggregation logic
print("\n[TEST 4] Checking fact_inventory aggregation...")
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT (material_code, plant_code)) as unique_combinations,
        SUM(qty_kg) as total_weight_kg
    FROM fact_inventory
""")).fetchone()

print(f"fact_inventory total rows: {result[0]:,}")
print(f"Unique material+plant combinations: {result[1]:,}")
print(f"Total weight (if summed directly): {result[2]:,.0f} kg")

# Now check what view does
result2 = engine.connect().execute(text("""
    SELECT SUM(current_qty_kg) as total_weight_kg
    FROM view_inventory_current
""")).fetchone()

print(f"Total weight (from view_inventory_current): {result2[0]:,.0f} kg")

if result[0] != result[1]:
    print(f"⚠️  WARNING: fact_inventory has {result[0] - result[1]:,} duplicate material+plant rows")
    print("   The view is grouping them, but the fact table shouldn't have duplicates!")

# Test 5: Check leadtime endpoint simulation
print("\n[TEST 5] Simulating leadtime /by-channel endpoint...")
result = engine.connect().execute(text("""
    SELECT 
        COALESCE(rz.dist_channel, '99') as channel,
        COUNT(*) as total_orders,
        COUNT(CASE WHEN fp.is_mto = TRUE THEN 1 END) as mto_orders,
        COUNT(CASE WHEN fp.is_mto = FALSE THEN 1 END) as mts_orders
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY COALESCE(rz.dist_channel, '99')
    ORDER BY channel
""")).fetchall()

print("Results by channel:")
total_after_join = sum(row[1] for row in result)
for row in result:
    print(f"  Channel {row[0]}: {row[1]:,} orders (MTO: {row[2]:,}, MTS: {row[3]:,})")

# Compare to base table
base_count = engine.connect().execute(text("""
    SELECT COUNT(*) FROM fact_production WHERE total_leadtime_days IS NOT NULL
""")).fetchone()[0]

print(f"\nBase count (fact_production with leadtime): {base_count:,}")
print(f"After JOIN (total across channels): {total_after_join:,}")

if total_after_join > base_count:
    inflation = ((total_after_join / base_count) - 1) * 100
    print(f"❌ INFLATION DETECTED: {inflation:.1f}% increase!")
    print("   ROOT CAUSE: raw_zrsd006 has duplicate materials, JOIN creates extra rows")
else:
    print("✅ No inflation in this query")

# Test 6: Check AR aggregations
print("\n[TEST 6] Checking AR aging aggregations...")
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total_rows,
        SUM(total_target) as sum_of_totals,
        SUM(COALESCE(target_1_30,0) + COALESCE(target_31_60,0) + 
            COALESCE(target_61_90,0) + COALESCE(target_91_120,0) + 
            COALESCE(target_121_180,0) + COALESCE(target_over_180,0) + 
            COALESCE(realization_not_due,0)) as sum_of_buckets
    FROM fact_ar_aging
""")).fetchone()

print(f"AR rows: {result[0]:,}")
print(f"SUM(total_target): {result[1]:,.0f}")
print(f"SUM(all buckets): {result[2]:,.0f}")

if abs(result[1] - result[2]) > 1000:
    print(f"⚠️  Bucket totals don't match total_target!")
else:
    print("✅ AR buckets sum correctly")

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
