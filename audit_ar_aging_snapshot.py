"""
AR Aging Snapshot Isolation Audit
Investigates the AR aging bucket distribution data inflation issue
"""
from src.api.deps import get_db
from sqlalchemy import text

db = next(get_db())

print("=" * 80)
print("🔍 AR AGING SNAPSHOT ISOLATION AUDIT")
print("=" * 80)

# Check table structure
print('\n1️⃣  FACT_AR_AGING TABLE STRUCTURE')
print("-" * 80)
result = db.execute(text("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'fact_ar_aging'
    ORDER BY ordinal_position
""")).fetchall()
for row in result:
    print(f'  {row[0]:30s} {row[1]}')

# Check distinct snapshot_date values
print('\n2️⃣  DISTINCT SNAPSHOT_DATE VALUES')
print("-" * 80)
result = db.execute(text("""
    SELECT snapshot_date, COUNT(*) as count
    FROM fact_ar_aging
    GROUP BY snapshot_date
    ORDER BY snapshot_date DESC
""")).fetchall()
snapshots = []
for row in result:
    snapshots.append(row[0])
    print(f'  {row[0]}: {row[1]} rows')

# Check total amounts per snapshot for 1-30 Days bucket
print('\n3️⃣  TOTAL AMOUNTS PER SNAPSHOT (1-30 Days Bucket)')
print("-" * 80)
result = db.execute(text("""
    SELECT 
        snapshot_date,
        SUM(COALESCE(target_1_30, 0)) as total_1_30_days,
        SUM(COALESCE(total_target, 0)) as total_target
    FROM fact_ar_aging
    GROUP BY snapshot_date
    ORDER BY snapshot_date DESC
""")).fetchall()
snapshot_totals = []
for row in result:
    snapshot_totals.append((row[0], row[1], row[2]))
    print(f'  {row[0]}: {row[1]:,.0f} VND (1-30 Days) | Total AR: {row[2]:,.0f} VND')

# CRITICAL TEST: What is the current API returning?
print('\n4️⃣  CURRENT API QUERY (WITHOUT snapshot_date filter)')
print("-" * 80)
r = db.execute(text("""
    SELECT 
        SUM(COALESCE(realization_not_due, 0)),
        SUM(COALESCE(target_1_30, 0)), SUM(COALESCE(target_31_60, 0)),
        SUM(COALESCE(target_61_90, 0)), SUM(COALESCE(target_91_120, 0)),
        SUM(COALESCE(target_121_180, 0)), SUM(COALESCE(target_over_180, 0)),
        SUM(COALESCE(realization_1_30, 0)), SUM(COALESCE(realization_31_60, 0)),
        SUM(COALESCE(realization_61_90, 0)), SUM(COALESCE(realization_91_120, 0)),
        SUM(COALESCE(realization_121_180, 0)), SUM(COALESCE(realization_over_180, 0))
    FROM fact_ar_aging
""")).fetchone()

print(f'  Not Due:       {r[0]:>20,.0f} VND')
print(f'  1-30 Days:     {r[1]:>20,.0f} VND ⚠️  (TARGET)')
print(f'  31-60 Days:    {r[2]:>20,.0f} VND')
print(f'  61-90 Days:    {r[3]:>20,.0f} VND')
print(f'  91-120 Days:   {r[4]:>20,.0f} VND')
print(f'  121-180 Days:  {r[5]:>20,.0f} VND')
print(f'  >180 Days:     {r[6]:>20,.0f} VND')

# Now test with proper snapshot filtering
if snapshots:
    latest_snapshot = snapshots[0]
    print(f'\n5️⃣  CORRECTED QUERY (WITH snapshot_date = {latest_snapshot})')
    print("-" * 80)
    r = db.execute(text("""
        SELECT 
            SUM(COALESCE(realization_not_due, 0)),
            SUM(COALESCE(target_1_30, 0)), SUM(COALESCE(target_31_60, 0)),
            SUM(COALESCE(target_61_90, 0)), SUM(COALESCE(target_91_120, 0)),
            SUM(COALESCE(target_121_180, 0)), SUM(COALESCE(target_over_180, 0)),
            SUM(COALESCE(realization_1_30, 0)), SUM(COALESCE(realization_31_60, 0)),
            SUM(COALESCE(realization_61_90, 0)), SUM(COALESCE(realization_91_120, 0)),
            SUM(COALESCE(realization_121_180, 0)), SUM(COALESCE(realization_over_180, 0))
        FROM fact_ar_aging
        WHERE snapshot_date = :snapshot_date
    """), {"snapshot_date": latest_snapshot}).fetchone()
    
    print(f'  Not Due:       {r[0]:>20,.0f} VND')
    print(f'  1-30 Days:     {r[1]:>20,.0f} VND ✅ (TARGET)')
    print(f'  31-60 Days:    {r[2]:>20,.0f} VND')
    print(f'  61-90 Days:    {r[3]:>20,.0f} VND')
    print(f'  91-120 Days:   {r[4]:>20,.0f} VND')
    print(f'  121-180 Days:  {r[5]:>20,.0f} VND')
    print(f'  >180 Days:     {r[6]:>20,.0f} VND')

# Calculate inflation multiplier
print('\n6️⃣  DATA INFLATION ANALYSIS')
print("-" * 80)
if len(snapshot_totals) > 0:
    # Get ALL snapshots total
    total_all_snapshots = db.execute(text("""
        SELECT SUM(COALESCE(target_1_30, 0))
        FROM fact_ar_aging
    """)).scalar()
    
    # Get LATEST snapshot total
    latest_snapshot_total = snapshot_totals[0][1]
    
    multiplier = total_all_snapshots / latest_snapshot_total if latest_snapshot_total > 0 else 0
    
    print(f'  Latest Snapshot (1-30 Days):  {latest_snapshot_total:>20,.0f} VND')
    print(f'  ALL Snapshots Sum (1-30 Days): {total_all_snapshots:>20,.0f} VND ⚠️')
    print(f'  Inflation Multiplier:          {multiplier:>20.2f}x')
    print(f'  Number of Snapshots:           {len(snapshots)} snapshots')

print('\n' + "=" * 80)
print('✅ AUDIT COMPLETE')
print("=" * 80)
