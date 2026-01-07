import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text, inspect

db = SessionLocal()

print("Columns in fact_ar_aging:")
inspector = inspect(db.bind)
cols = [c['name'] for c in inspector.get_columns('fact_ar_aging')]
for c in cols:
    print(f"  - {c}")

print("\n Sample data (first 3 rows):")
result = db.execute(text("SELECT * FROM fact_ar_aging LIMIT 3")).fetchall()
print(f"  Found {len(result)} rows")
if result:
    print(f"  Columns: {len(result[0])} values")
    
db.close()
