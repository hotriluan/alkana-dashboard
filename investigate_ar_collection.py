"""
Phase 2: AR Collection Investigation

Investigate why AR Collection dashboard shows empty display
despite having 93 rows in fact_ar_aging table.

Skills: database, data-analysis, backend-development
"""
import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    
    print("="*80)
    print("PHASE 2: AR COLLECTION INVESTIGATION")
    print("="*80)
    
    # Step 1: Check fact_ar_aging table
    print("\n[1] fact_ar_aging Table:")
    count = db.execute(text("SELECT COUNT(*) FROM fact_ar_aging")).scalar()
    print(f"  Total rows: {count:,}")
    
    if count > 0:
        # Sample data
        print("\n  Sample data:")
        result = db.execute(text("""
            SELECT id, division, customer_name, total_target, total_realization, 
                   collection_rate_pct, snapshot_date::text
            FROM fact_ar_aging
            LIMIT 5
        """)).fetchall()
        
        for r in result:
            print(f"    ID: {r[0]}, Division: {r[1]}, Customer: {r[2]}")
            print(f"      Target: {r[3]}, Realization: {r[4]}, Rate: {r[5]}%, Date: {r[6]}")
    else:
        print("  ⚠️ Table is empty!")
    
    # Step 2: Check view_ar_collection_summary
    print("\n[2] view_ar_collection_summary View:")
    try:
        view_count = db.execute(text("SELECT COUNT(*) FROM view_ar_collection_summary")).scalar()
        print(f"  Total rows: {view_count:,}")
        
        if view_count > 0:
            result = db.execute(text("""
                SELECT division, dist_channel, total_target, total_realization, 
                       collection_rate_pct, report_date::text
                FROM view_ar_collection_summary
            """)).fetchall()
            
            print("\n  Data:")
            for r in result:
                print(f"    Division: {r[0]}, Channel: {r[1]}")
                print(f"      Target: {r[2]:,.0f}, Realization: {r[3]:,.0f}, Rate: {r[4]}%")
        else:
            print("  ⚠️ View returns no rows!")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Step 3: Check view_ar_aging_detail
    print("\n[3] view_ar_aging_detail View:")
    try:
        detail_count = db.execute(text("SELECT COUNT(*) FROM view_ar_aging_detail")).scalar()
        print(f"  Total rows: {detail_count:,}")
        
        if detail_count > 0:
            result = db.execute(text("""
                SELECT division, customer_name, total_target, total_realization
                FROM view_ar_aging_detail
                LIMIT 3
            """)).fetchall()
            
            print("\n  Sample:")
            for r in result:
                print(f"    {r[0]}: {r[1]} - Target: {r[2]:,.0f}, Real: {r[3]:,.0f}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Step 4: Check raw_zrfi005
    print("\n[4] raw_zrfi005 (Source Data):")
    raw_count = db.execute(text("SELECT COUNT(*) FROM raw_zrfi005")).scalar()
    print(f"  Total rows: {raw_count:,}")
    
    if raw_count > 0:
        # Check snapshot dates
        snapshots = db.execute(text("""
            SELECT snapshot_date::text, COUNT(*) as cnt
            FROM raw_zrfi005
            WHERE snapshot_date IS NOT NULL
            GROUP BY snapshot_date
            ORDER BY snapshot_date DESC
            LIMIT 5
        """)).fetchall()
        
        print(f"\n  Available snapshots:")
        for s in snapshots:
            print(f"    {s[0]}: {s[1]:,} rows")
    else:
        print("  ⚠️ No source data available!")
    
    # Step 5: Check API endpoint
    print("\n[5] API Endpoint Analysis:")
    print("  Backend: /api/v1/dashboards/ar-aging/summary")
    print("  Expected: ARCollectionTotal with divisions array")
    
    # Summary
    print("\n" + "="*80)
    print("INVESTIGATION SUMMARY")
    print("="*80)
    
    if count == 0:
        print("❌ ROOT CAUSE: fact_ar_aging table is EMPTY")
        print("   Solution: Need to transform ZRFI005 data")
        print("   Action: Run transform_zrfi005()")
    elif view_count == 0:
        print("❌ ROOT CAUSE: Views return no data")
        print("   Possible causes:")
        print("     - View definition filters out all data")
        print("     - JOIN conditions don't match")
        print("   Action: Check view definitions in src/db/views.py")
    else:
        print("✅ Data exists in fact_ar_aging")
        print(f"   Rows: {count:,}")
        print("   Issue might be:")
        print("     - Frontend not calling correct endpoint")
        print("     - Frontend not rendering response")
        print("     - API authentication issue")
    
    print("="*80)
    
    db.close()

if __name__ == "__main__":
    main()
