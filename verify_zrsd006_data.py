import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

print("VERIFICATION: raw_zrsd006 has distribution channel data")
print("=" * 70)

# 1. Check data exists
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(material) as has_material,
        COUNT(dist_channel) as has_channel
    FROM raw_zrsd006
""")).fetchone()

print(f"1. Data in raw_zrsd006:")
print(f"   Total rows: {result[0]}")
print(f"   With material: {result[1]} ({result[1]*100/result[0]:.1f}%)")
print(f"   With dist_channel: {result[2]} ({result[2]*100/result[0]:.1f}%)")

# 2. Distribution channel breakdown
print(f"\n2. Distribution channels:")
result = engine.connect().execute(text("""
    SELECT dist_channel, COUNT(*) 
    FROM raw_zrsd006 
    WHERE dist_channel IS NOT NULL
    GROUP BY dist_channel 
    ORDER BY dist_channel
""")).fetchall()

for row in result:
    ch_name = {'11': 'Industry', '12': 'Over Sea', '13': 'Retail', '15': 'Project'}.get(row[0], row[0])
    print(f"   {row[0]} ({ch_name}): {row[1]} materials")

# 3. Test JOIN with fact_production
print(f"\n3. Testing JOIN with fact_production:")
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN rz.dist_channel IS NOT NULL THEN 1 END) as matched,
        ROUND(COUNT(CASE WHEN rz.dist_channel IS NOT NULL THEN 1 END)*100.0/COUNT(*), 1) as pct
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()

print(f"   Total orders: {result[0]}")
print(f"   Matched: {result[1]} ({result[2]}%)")

# 4. Show sample grouping
if result[2] > 0:
    print(f"\n4. Sample grouping by channel:")
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
    
    for row in result:
        ch_name = {'11': 'Industry', '12': 'Over Sea', '13': 'Retail', '15': 'Project', '99': 'No Data'}.get(row[0], row[0])
        print(f"   {ch_name} - {row[1]}: {row[2]} orders")

print("\n" + "=" * 70)
if result[2] > 50:
    print("SUCCESS! Can use raw_zrsd006 for distribution channel grouping!")
else:
    print("WARNING: Low match rate. Need to investigate material code format.")
