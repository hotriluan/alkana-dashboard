"""
Test channel grouping query directly from database
"""
import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

print("Testing Distribution Channel Grouping Query")
print("=" * 80)

result = engine.connect().execute(text("""
    SELECT 
        CAST(COALESCE(rz.dist_channel, '99') AS TEXT) as channel,
        CASE 
            WHEN COALESCE(rz.dist_channel, '99') = '11' THEN 'Industry'
            WHEN COALESCE(rz.dist_channel, '99') = '12' THEN 'Over Sea'
            WHEN COALESCE(rz.dist_channel, '99') = '13' THEN 'Retail'
            WHEN COALESCE(rz.dist_channel, '99') = '15' THEN 'Project'
            ELSE 'No Channel Data'
        END as channel_name,
        -- MTO metrics
        COUNT(CASE WHEN fp.is_mto = TRUE THEN 1 END) as mto_orders,
        ROUND(AVG(CASE WHEN fp.is_mto = TRUE THEN fp.total_leadtime_days END), 1) as mto_avg_leadtime,
        ROUND(COUNT(CASE WHEN fp.is_mto = TRUE AND fp.leadtime_status='ON_TIME' THEN 1 END)*100.0/
              NULLIF(COUNT(CASE WHEN fp.is_mto = TRUE THEN 1 END), 0), 1) as mto_on_time_pct,
        -- MTS metrics
        COUNT(CASE WHEN fp.is_mto = FALSE THEN 1 END) as mts_orders,
        ROUND(AVG(CASE WHEN fp.is_mto = FALSE THEN fp.total_leadtime_days END), 1) as mts_avg_leadtime,
        ROUND(COUNT(CASE WHEN fp.is_mto = FALSE AND fp.leadtime_status='ON_TIME' THEN 1 END)*100.0/
              NULLIF(COUNT(CASE WHEN fp.is_mto = FALSE THEN 1 END), 0), 1) as mts_on_time_pct,
        -- Total
        COUNT(*) as total_orders,
        ROUND(AVG(fp.total_leadtime_days), 1) as avg_total_leadtime
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY COALESCE(rz.dist_channel, '99')
    ORDER BY COALESCE(rz.dist_channel, '99')
""")).fetchall()

print(f"✅ Query returned {len(result)} rows\n")

# Display in table format
print(f"{'Channel':<20s} {'MTO':>6s} {'MTO Avg':>9s} {'MTO On%':>8s} {'MTS':>6s} {'MTS Avg':>9s} {'MTS On%':>8s} {'Total':>7s} {'Avg':>8s}")
print("-" * 80)

for row in result:
    mto_avg = f"{row[3]:.1f}d" if row[3] else "-"
    mto_on = f"{row[4]:.1f}%" if row[4] else "-"
    mts_avg = f"{row[6]:.1f}d" if row[6] else "-"
    mts_on = f"{row[7]:.1f}%" if row[7] else "-"
    total_avg = f"{row[9]:.1f}d" if row[9] else "-"
    
    print(f"{row[1]:<20s} {row[2]:>6d} {mto_avg:>9s} {mto_on:>8s} {row[5]:>6d} {mts_avg:>9s} {mts_on:>8s} {row[8]:>7d} {total_avg:>8s}")

print("\n" + "=" * 80)
print("✅ SUCCESS! Each channel now has ONE row with separate MTO/MTS columns!")
print("=" * 80)
