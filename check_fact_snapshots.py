"""Quick check: How many snapshots in fact_ar_aging?"""
from src.db.connection import get_db
from sqlalchemy import text

db = next(get_db())
result = db.execute(text("""
    SELECT snapshot_date, COUNT(*) 
    FROM fact_ar_aging 
    GROUP BY snapshot_date 
    ORDER BY snapshot_date
""")).fetchall()

print("\nfact_ar_aging snapshot distribution:")
for row in result:
    print(f"  {row[0]}: {row[1]} records")

total = db.execute(text("SELECT COUNT(*) FROM fact_ar_aging")).scalar()
print(f"\nTotal: {total} records")
