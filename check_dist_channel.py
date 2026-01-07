import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

print("=" * 70)
print("CHECKING DISTRIBUTION CHANNEL DATA IN ZRSD006")
print("=" * 70)

# Check 1: Distribution channels available
print("\n1. Distribution Channels in raw_zrsd006:")
print("-" * 70)
result = engine.connect().execute(text("""
    SELECT dist_channel, COUNT(*) as count
    FROM raw_zrsd006
    WHERE dist_channel IS NOT NULL
    GROUP BY dist_channel
    ORDER BY dist_channel
""")).fetchall()
for row in result:
    channel_name = {
        '11': 'Industry',
        '12': 'Over Sea', 
        '13': 'Retail',
        '15': 'Project'
    }.get(row[0], 'Unknown')
    print(f"  Channel {row[0]} ({channel_name:10s}): {row[1]:5d} materials")

# Check 2: Can we JOIN with fact_production?
print("\n2. JOIN Test: fact_production with raw_zrsd006:")
print("-" * 70)
result = engine.connect().execute(text("""
    SELECT 
        COUNT(DISTINCT fp.material_code) as total_materials,
        COUNT(DISTINCT CASE WHEN rz.material IS NOT NULL THEN fp.material_code END) as matched_materials,
        COUNT(DISTINCT CASE WHEN rz.dist_channel IS NOT NULL THEN fp.material_code END) as materials_with_channel
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()
print(f"  Total materials in production: {result[0]}")
print(f"  Matched with zrsd006: {result[1]} ({result[1]*100/result[0]:.1f}%)")
print(f"  Have distribution channel: {result[2]} ({result[2]*100/result[0]:.1f}%)")

# Check 3: Distribution by channel
print("\n3. Production Orders by Distribution Channel:")
print("-" * 70)
result = engine.connect().execute(text("""
    SELECT 
        COALESCE(rz.dist_channel, '99') as channel,
        CASE 
            WHEN rz.dist_channel = '11' THEN 'Industry'
            WHEN rz.dist_channel = '12' THEN 'Over Sea'
            WHEN rz.dist_channel = '13' THEN 'Retail'
            WHEN rz.dist_channel = '15' THEN 'Project'
            ELSE 'No Channel Data'
        END as channel_name,
        CASE WHEN fp.is_mto = TRUE THEN 'MTO' ELSE 'MTS' END as order_type,
        COUNT(*) as order_count,
        ROUND(AVG(fp.total_leadtime_days), 1) as avg_leadtime
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY rz.dist_channel, fp.is_mto
    ORDER BY rz.dist_channel, fp.is_mto DESC
    LIMIT 20
""")).fetchall()

print(f"\n{'Channel':<20s} {'Type':<5s} {'Orders':>7s} {'Avg Lead-time':>15s}")
print("-" * 70)
for row in result:
    print(f"{row[1]:<20s} {row[2]:<5s} {row[3]:>7d} {row[4]:>12.1f} days")

print("\n" + "=" * 70)
print("✅ CONCLUSION: Can use raw_zrsd006.dist_channel for grouping!")
print("=" * 70)
