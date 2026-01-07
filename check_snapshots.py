"""Check snapshot_date in raw_zrfi005"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/alkana_dashboard')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check snapshots with data
    print("=== SNAPSHOT_DATE in raw_zrfi005 ===\n")
    result = conn.execute(text('''
        SELECT snapshot_date, COUNT(*) as row_count
        FROM raw_zrfi005 
        WHERE snapshot_date IS NOT NULL 
        GROUP BY snapshot_date 
        ORDER BY snapshot_date DESC
    ''')).fetchall()
    
    if result:
        print(f"Found {len(result)} snapshots:")
        for r in result:
            print(f"  {r[0]}: {r[1]:,} rows")
    else:
        print("NO snapshots found (all snapshot_date are NULL)")
    
    # Total stats
    print("\n=== OVERALL STATS ===")
    result2 = conn.execute(text('''
        SELECT 
            COUNT(*) as total_rows,
            COUNT(snapshot_date) as rows_with_snapshot,
            COUNT(*) - COUNT(snapshot_date) as rows_without_snapshot
        FROM raw_zrfi005
    ''')).fetchone()
    
    print(f"Total rows in raw_zrfi005: {result2[0]:,}")
    print(f"Rows WITH snapshot_date: {result2[1]:,}")
    print(f"Rows WITHOUT snapshot_date (NULL): {result2[2]:,}")
    
    if result2[2] > 0:
        print("\n⚠️  WARNING: Some rows have NULL snapshot_date!")
        print("These rows won't appear in the snapshots dropdown.")
