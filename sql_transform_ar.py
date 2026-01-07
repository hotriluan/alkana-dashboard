"""
CLAUDE KIT: Direct SQL Transform - Bypass Python import issues
Manually copy data from raw_zrfi005 to fact_ar_aging
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:password123@localhost:5432/alkana_dashboard"
engine = create_engine(DATABASE_URL)

print("=" * 70)
print("CLAUDE KIT: Direct SQL AR Transform")
print("Skills: Database, SQL, Sequential Thinking")
print("=" * 70)

with engine.begin() as conn:
    # Step 1: Clear fact table
    print("\n[STEP 1] Clear fact_ar_aging")
    result = conn.execute(text("DELETE FROM fact_ar_aging"))
    print(f"  Deleted {result.rowcount} rows")
    
    # Step 2: Insert from raw to fact
    print("\n[STEP 2] Transform raw_zrfi005 → fact_ar_aging")
    result = conn.execute(text("""
        INSERT INTO fact_ar_aging (
            dist_channel,
            cust_group,
            salesman_name,
            customer_name,
            currency,
            target_1_30,
            target_31_60,
            target_61_90,
            target_91_120,
            target_121_180,
            target_over_180,
            total_target,
            realization_not_due,
            realization_1_30,
            realization_31_60,
            realization_61_90,
            realization_91_120,
            realization_121_180,
            realization_over_180,
            total_realization,
            report_date,
            snapshot_date,
            raw_id
        )
        SELECT 
            dist_channel,
            cust_group,
            salesman_name,
            customer_name,
            currency,
            target_1_30::numeric,
            target_31_60::numeric,
            target_61_90::numeric,
            target_91_120::numeric,
            target_121_180::numeric,
            target_over_180::numeric,
            total_target::numeric,
            realization_not_due::numeric,
            realization_1_30::numeric,
            realization_31_60::numeric,
            realization_61_90::numeric,
            realization_91_120::numeric,
            realization_121_180::numeric,
            realization_over_180::numeric,
            total_realization::numeric,
            CURRENT_DATE as report_date,
            snapshot_date,
            id as raw_id
        FROM raw_zrfi005
        WHERE snapshot_date IS NOT NULL
    """))
    print(f"  ✅ Inserted {result.rowcount} rows")
    
    # Step 3: Verify
    print("\n[STEP 3] Verify fact_ar_aging")
    result = conn.execute(text("""
        SELECT 
            snapshot_date,
            COUNT(*) as rows,
            SUM(total_target) as target,
            SUM(total_realization) as realization,
            ROUND(SUM(total_realization) / NULLIF(SUM(total_target), 0) * 100, 2) as collection_rate
        FROM fact_ar_aging
        GROUP BY snapshot_date
        ORDER BY snapshot_date DESC
    """)).fetchall()
    
    for row in result:
        print(f"  {row[0]}: {row[1]} rows")
        print(f"    Target: {row[2]:,.0f}")
        print(f"    Realization: {row[3]:,.0f}")
        print(f"    Collection Rate: {row[4]}%")

print("\n" + "=" * 70)
print("✅ TRANSFORM COMPLETE")
print("=" * 70)
