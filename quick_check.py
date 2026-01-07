import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

# Quick check
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(material) as has_mat,
        COUNT(dist_channel) as has_ch
    FROM raw_zrsd006
""")).fetchone()

print(f"raw_zrsd006: {result[0]} rows")
print(f"  material: {result[1]} ({result[1]*100/result[0]:.0f}%)")
print(f"  dist_channel: {result[2]} ({result[2]*100/result[0]:.0f}%)")

# Test JOIN
result = engine.connect().execute(text("""
    SELECT 
        COALESCE(rz.dist_channel, '99') as ch,
        CASE WHEN fp.is_mto THEN 'MTO' ELSE 'MTS' END as type,
        COUNT(*) as cnt
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY rz.dist_channel, fp.is_mto
    ORDER BY rz.dist_channel, fp.is_mto DESC
""")).fetchall()

print("\nGrouping:")
for row in result:
    ch_map = {'11': 'Industry', '12': 'Over Sea', '13': 'Retail', '15': 'Project', '99': 'No Data'}
    print(f"  {ch_map.get(row[0], row[0]):<12s} {row[1]}: {row[2]:4d} orders")
