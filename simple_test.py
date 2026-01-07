import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

result = engine.connect().execute(text("""
    SELECT 
        COALESCE(rz.dist_channel, '99') as channel,
        COUNT(CASE WHEN fp.is_mto = TRUE THEN 1 END) as mto_orders,
        COUNT(CASE WHEN fp.is_mto = FALSE THEN 1 END) as mts_orders,
        COUNT(*) as total_orders
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY COALESCE(rz.dist_channel, '99')
    ORDER BY COALESCE(rz.dist_channel, '99')
""")).fetchall()

print(f"Total channels: {len(result)}")
print("")
for row in result:
    ch_name = {'11': 'Industry', '12': 'Over Sea', '13': 'Retail', '15': 'Project', '99': 'No Data'}.get(row[0], row[0])
    print(f"{ch_name:15s} - MTO: {row[1]:4d}, MTS: {row[2]:4d}, Total: {row[3]:4d}")

print("")
print("SUCCESS: Each channel = 1 row!")
