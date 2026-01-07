import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

# Quick check: Distribution channels in zrsd006
result = engine.connect().execute(text("""
    SELECT dist_channel, COUNT(*) 
    FROM raw_zrsd006
    WHERE dist_channel IS NOT NULL
    GROUP BY dist_channel
    ORDER BY dist_channel
""")).fetchall()

print("Distribution Channels in raw_zrsd006:")
for row in result:
    print(f"  {row[0]}: {row[1]} materials")

# Check JOIN coverage
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN rz.dist_channel IS NOT NULL THEN 1 END) as with_channel
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()

print(f"\nJOIN Coverage:")
print(f"  Total orders: {result[0]}")
print(f"  With channel data: {result[1]} ({result[1]*100/result[0]:.1f}%)")

# Sample grouping
result = engine.connect().execute(text("""
    SELECT 
        COALESCE(rz.dist_channel, '99') as ch,
        COUNT(*) as cnt
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY rz.dist_channel
    ORDER BY cnt DESC
""")).fetchall()

print(f"\nOrders by Channel:")
for row in result:
    ch_name = {'11': 'Industry', '12': 'Over Sea', '13': 'Retail', '15': 'Project', '99': 'No Data'}.get(row[0], row[0])
    print(f"  {row[0]} ({ch_name}): {row[1]} orders")
