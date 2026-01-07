import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

# Test 1: Check if JOIN works
print("=" * 60)
print("TEST 1: Checking fact_delivery JOIN")
print("=" * 60)
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT fp.sales_order) as distinct_so,
        COUNT(fd.so_number) as matched_deliveries
    FROM fact_production fp
    LEFT JOIN fact_delivery fd ON fp.sales_order = fd.so_number
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()
print(f"Total production orders: {result[0]}")
print(f"Distinct sales orders: {result[1]}")
print(f"Matched deliveries: {result[2]}")
print()

# Test 2: Check customer groups
print("=" * 60)
print("TEST 2: Customer groups from fact_delivery")
print("=" * 60)
result = engine.connect().execute(text("""
    SELECT 
        COALESCE(fd.cust_group, '99') as channel,
        COUNT(*) as count
    FROM fact_production fp
    LEFT JOIN fact_delivery fd ON fp.sales_order = fd.so_number
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY COALESCE(fd.cust_group, '99')
    ORDER BY count DESC
    LIMIT 10
""")).fetchall()
print("Customer groups found:")
for row in result:
    print(f"  {row[0]}: {row[1]} orders")
print()

# Test 3: Full query (simplified)
print("=" * 60)
print("TEST 3: Full by-channel query")
print("=" * 60)
try:
    result = engine.connect().execute(text("""
        SELECT 
            CAST(COALESCE(fd.cust_group, '99') AS TEXT) as channel,
            CASE 
                WHEN COALESCE(fd.cust_group, '99') = '11' THEN 'Industry'
                WHEN COALESCE(fd.cust_group, '99') = '13' THEN 'Retail'
                WHEN COALESCE(fd.cust_group, '99') = '15' THEN 'Project'
                ELSE 'Other'
            END as channel_name,
            CASE WHEN fp.is_mto = TRUE THEN 'MTO' ELSE 'MTS' END as order_type,
            COUNT(*) as order_count
        FROM fact_production fp
        LEFT JOIN fact_delivery fd ON fp.sales_order = fd.so_number
        WHERE fp.total_leadtime_days IS NOT NULL
        GROUP BY COALESCE(fd.cust_group, '99'), fp.is_mto
        ORDER BY COALESCE(fd.cust_group, '99'), fp.is_mto DESC
    """)).fetchall()
    print(f"✅ Query SUCCESS! Found {len(result)} combinations:")
    for row in result:
        print(f"  {row[1]} ({row[0]}) - {row[2]}: {row[3]} orders")
except Exception as e:
    print(f"❌ Query FAILED: {e}")
    import traceback
    traceback.print_exc()
