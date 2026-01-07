from src.db.connection import engine
from sqlalchemy import text

# Find AR tables
tables = engine.connect().execute(text(
    "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE '%ar%'"
)).fetchall()

print("AR-related tables:")
for t in tables:
    print(f"  - {t[0]}")

# Check if fact_ar_aging exists
ar_tables = [t[0] for t in tables]
if 'fact_ar_aging' in ar_tables:
    columns = engine.connect().execute(text(
        "SELECT * FROM fact_ar_aging LIMIT 1"
    )).fetchone()
    print(f"\nfact_ar_aging columns: {columns._fields}")
else:
    print("\nfact_ar_aging table does NOT exist!")
