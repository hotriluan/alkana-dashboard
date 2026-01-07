import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

print("Testing JOIN with dim_material...")
print("=" * 70)

# Test JOIN coverage
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total_orders,
        COUNT(CASE WHEN dm.dist_channel IS NOT NULL THEN 1 END) as with_channel,
        ROUND(COUNT(CASE WHEN dm.dist_channel IS NOT NULL THEN 1 END)*100.0/COUNT(*), 1) as coverage_pct
    FROM fact_production fp
    LEFT JOIN dim_material dm ON fp.material_code = dm.material_code
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()

print(f"JOIN Coverage:")
print(f"  Total orders: {result[0]}")
print(f"  With channel: {result[1]}")
print(f"  Coverage: {result[2]}%")
print()

# Test grouping
result = engine.connect().execute(text("""
    SELECT 
        COALESCE(dm.dist_channel, '99') as channel,
        CASE 
            WHEN dm.dist_channel = '11' THEN 'Industry'
            WHEN dm.dist_channel = '12' THEN 'Over Sea'
            WHEN dm.dist_channel = '13' THEN 'Retail'
            WHEN dm.dist_channel = '15' THEN 'Project'
            ELSE 'No Channel Data'
        END as channel_name,
        CASE WHEN fp.is_mto = TRUE THEN 'MTO' ELSE 'MTS' END as order_type,
        COUNT(*) as order_count,
        ROUND(AVG(fp.total_leadtime_days), 1) as avg_leadtime
    FROM fact_production fp
    LEFT JOIN dim_material dm ON fp.material_code = dm.material_code
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY dm.dist_channel, fp.is_mto
    ORDER BY dm.dist_channel, fp.is_mto DESC
""")).fetchall()

print(f"Orders by Distribution Channel:")
print(f"{'Channel':<20s} {'Type':<5s} {'Orders':>7s} {'Avg Lead-time':>15s}")
print("-" * 70)
for row in result:
    print(f"{row[1]:<20s} {row[2]:<5s} {row[3]:>7d} {row[4]:>12.1f} days")

print("\n" + "=" * 70)
if result and any(r[0] != '99' for r in result):
    print("✅ SUCCESS! dim_material has distribution channel data!")
    print("   Recommendation: Use dim_material for JOIN")
else:
    print("❌ FAILED: dim_material also has no channel data")
    print("   Need to check import process")
