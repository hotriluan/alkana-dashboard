"""
ETL Data Duplication Audit

Skills: backend-development, databases
CLAUDE.md: KISS - Systematic audit of all fact tables

Issue: AR and inventory data duplicated 3x after transform
- Total AR: 181B (should be ~60B)
- Total Weight: 1396.5K kg (should be ~465K kg)
"""
import sys
sys.path.insert(0, '.')

from src.db.connection import engine
from sqlalchemy import text

print("=" * 80)
print("ETL DATA DUPLICATION AUDIT")
print("=" * 80)

# Step 1: Check all fact tables for row counts
print("\n[STEP 1] FACT TABLES ROW COUNTS")
print("-" * 80)

fact_tables = [
    'fact_ar_aging',
    'fact_inventory',
    'fact_mto_orders',
    'fact_billing',
    'fact_production_chain',
    'fact_alerts',
    'fact_lead_time'
]

for table in fact_tables:
    try:
        count = engine.connect().execute(text(f'SELECT COUNT(*) FROM {table}')).fetchone()[0]
        print(f"{table:30s}: {count:,} rows")
    except Exception as e:
        print(f"{table:30s}: ERROR - {e}")

# Step 2: Check for duplicate records in fact_ar_aging
print("\n[STEP 2] CHECKING DUPLICATES IN fact_ar_aging")
print("-" * 80)

try:
    # Check if same customer appears multiple times
    result = engine.connect().execute(text("""
        SELECT customer_code, COUNT(*) as count
        FROM fact_ar_aging
        GROUP BY customer_code
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 5
    """)).fetchall()
    
    if result:
        print("❌ DUPLICATES FOUND!")
        print("Customers with duplicate records:")
        for r in result:
            print(f"  {r[0]}: {r[1]} records")
    else:
        print("✅ No duplicates found")
        
    # Check total AR sum
    total_ar = engine.connect().execute(text("""
        SELECT SUM(total_ar) FROM fact_ar_aging
    """)).fetchone()[0]
    
    print(f"\nTotal AR in database: {total_ar:,.2f}")
    print("Expected: ~60,000,000,000 (60B)")
    
    if total_ar > 150_000_000_000:
        print("❌ PROBLEM: Total AR is 3x expected value!")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Step 3: Check for duplicate records in fact_inventory
print("\n[STEP 3] CHECKING DUPLICATES IN fact_inventory")
print("-" * 80)

try:
    # Check if same material+plant appears multiple times
    result = engine.connect().execute(text("""
        SELECT material, plant, COUNT(*) as count
        FROM fact_inventory
        GROUP BY material, plant
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 5
    """)).fetchall()
    
    if result:
        print("❌ DUPLICATES FOUND!")
        print("Material+Plant with duplicate records:")
        for r in result:
            print(f"  {r[0]} at Plant {r[1]}: {r[2]} records")
    else:
        print("✅ No duplicates found")
        
    # Check total weight
    total_weight = engine.connect().execute(text("""
        SELECT SUM(quantity_kg) FROM fact_inventory
    """)).fetchone()[0]
    
    print(f"\nTotal weight in database: {total_weight:,.2f} kg")
    print("Expected: ~465,000 kg")
    
    if total_weight > 1_000_000:
        print("❌ PROBLEM: Total weight is 3x expected value!")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Step 4: Check transform execution history
print("\n[STEP 4] CHECKING TRANSFORM EXECUTION PATTERN")
print("-" * 80)

print("\nChecking if truncate is being called...")
print("Review src/etl/transform.py:")
print("1. Does transform_all() call truncate_warehouse()?")
print("2. Does truncate_warehouse() clear ALL fact tables?")
print("3. Are there any conditions that skip truncate?")

# Step 5: Check for multiple transform runs
print("\n[STEP 5] DETECTING MULTIPLE TRANSFORM RUNS")
print("-" * 80)

try:
    # Check alerts - each transform creates new alerts
    alert_count = engine.connect().execute(text("""
        SELECT COUNT(*) FROM fact_alerts
    """)).fetchone()[0]
    
    print(f"Total alerts: {alert_count}")
    
    # If we ran transform 3 times, we'd have ~3500 alerts (1182 * 3)
    if alert_count > 3000:
        print("❌ LIKELY RAN TRANSFORM 3+ TIMES WITHOUT TRUNCATE!")
    elif alert_count > 2000:
        print("⚠️  LIKELY RAN TRANSFORM 2 TIMES")
    else:
        print("✅ Alerts count suggests 1 transform run")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

print("""
LIKELY CAUSES:
1. transform_all() not calling truncate_warehouse()
2. truncate_warehouse() not clearing all tables
3. Running 'transform' command multiple times without truncate
4. ETL inserting duplicates within single run

SOLUTION:
1. Always run: python -m src.main run (full pipeline with truncate)
2. OR manually truncate before transform:
   - python -m src.main truncate
   - python -m src.main transform

IMMEDIATE FIX:
Run truncate + transform to clean data:
   python -m src.main truncate && python -m src.main transform
""")

print("=" * 80)
