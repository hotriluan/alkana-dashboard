"""Check ZRFI005 duplicates"""
from src.db.connection import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check duplicates for 2026-01-08
    r = conn.execute(text("""
        SELECT customer_name, COUNT(*) as cnt
        FROM raw_zrfi005 
        WHERE snapshot_date = '2026-01-08'
        GROUP BY customer_name, dist_channel, cust_group, salesman_name
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
    """))
    
    dupes = list(r)
    
    if dupes:
        print(f"Found {len(dupes)} duplicated business keys:")
        for row in dupes[:10]:
            print(f"  {row[0]}: {row[1]} times")
    else:
        print("✅ No duplicates found in raw_zrfi005!")
    
    # Check total counts by snapshot
    r2 = conn.execute(text("""
        SELECT snapshot_date, COUNT(*) 
        FROM raw_zrfi005 
        GROUP BY snapshot_date 
        ORDER BY snapshot_date
    """))
    
    print("\nSnapshot counts:")
    for row in r2:
        print(f"  {row[0]}: {row[1]} records")
