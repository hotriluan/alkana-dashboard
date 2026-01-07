import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("Tables that exist:")
result = db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE '%billing%' OR tablename LIKE '%sales%'")).fetchall()
for r in result:
    print(f"  - {r[0]}")

print("\nColumns in fact_billing (if exists):")
try:
    result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='fact_billing' ORDER BY ordinal_position")).fetchall()
    for r in result:
        print(f"  - {r[0]}")
except Exception as e:
    print(f"  Table doesn't exist: {e}")

print("\nSample from view_sales_performance:")
try:
    result = db.execute(text("SELECT * FROM view_sales_performance LIMIT 2")).fetchall()
    print(f"  Rows: {len(result)}")
    if result:
        print(f"  Columns: {len(result[0])} values")
except Exception as e:
    print(f"  Error: {e}")

db.close()
