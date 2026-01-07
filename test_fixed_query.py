import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

print("Testing fixed query with so_reference...")
print("=" * 60)

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
        COUNT(*) as order_count,
        ROUND(AVG(fp.total_leadtime_days), 1) as avg_total
    FROM fact_production fp
    LEFT JOIN fact_delivery fd ON fp.sales_order = fd.so_reference
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY COALESCE(fd.cust_group, '99'), fp.is_mto
    ORDER BY COALESCE(fd.cust_group, '99'), fp.is_mto DESC
""")).fetchall()

print(f"✅ SUCCESS! Found {len(result)} channel/type combinations:\n")
for row in result:
    print(f"  {row[1]:10s} ({row[0]}) - {row[2]:3s}: {row[3]:4d} orders, avg {row[4]:4.1f} days")
