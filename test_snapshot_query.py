"""Simulate AR Aging query with snapshot filter"""
from src.db.connection import get_db
from sqlalchemy import text

db = next(get_db())

for snapshot in ['2026-01-07', '2026-01-08']:
    print(f"\n=== Snapshot: {snapshot} ===")
    
    results = db.execute(text("""
        SELECT 
            CASE dist_channel
                WHEN '11' THEN 'Industry'
                WHEN '13' THEN 'Retails'
                WHEN '15' THEN 'Project'
                ELSE 'Other'
            END as division,
            dist_channel,
            SUM(COALESCE(total_target, 0)) as total_target,
            SUM(COALESCE(total_realization, 0)) as total_realization,
            CASE 
                WHEN SUM(COALESCE(total_target, 0)) > 0 
                THEN ROUND((SUM(COALESCE(total_realization, 0)) / SUM(total_target) * 100)::numeric, 0)
                ELSE 0 
            END as collection_rate_pct,
            MAX(report_date) as report_date
        FROM fact_ar_aging
        WHERE snapshot_date = :snapshot_date
        GROUP BY dist_channel
        ORDER BY 
            CASE dist_channel
                WHEN '11' THEN 1
                WHEN '13' THEN 2
                WHEN '15' THEN 3
                ELSE 4
            END
    """), {"snapshot_date": snapshot}).fetchall()
    
    total_target = sum(r[2] for r in results)
    total_real = sum(r[3] for r in results)
    
    print(f"Total Target: {total_target:,.0f}")
    print(f"Total Realization: {total_real:,.0f}")
    print(f"Divisions:")
    for r in results:
        print(f"  {r[0]} ({r[1]}): {r[2]:,.0f} / {r[3]:,.0f} ({r[4]}%)")
