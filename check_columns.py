import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("Columns in view_sales_performance:")
result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='view_sales_performance' ORDER BY ordinal_position")).fetchall()
for r in result:
    print(f"  - {r[0]}")

print("\nColumns in fact_p02_p01_yield:")
result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='fact_p02_p01_yield' ORDER BY ordinal_position")).fetchall()
for r in result:
    print(f"  - {r[0]}")

db.close()
