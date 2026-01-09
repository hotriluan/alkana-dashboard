"""Clean up bad NULL-date records from raw_zrsd002 and re-transform"""
from src.db.connection import get_db
from sqlalchemy import text
from src.etl.transform import Transformer

db = next(get_db())

print("=== Cleaning bad records ===")
# Delete NULL billing_date records (loaded with broken headers)
deleted = db.execute(text("""
    DELETE FROM raw_zrsd002 
    WHERE billing_date IS NULL
""")).rowcount
db.commit()
print(f"✓ Deleted {deleted} records with NULL billing_date")

# Check raw data now
total_raw = db.execute(text("SELECT COUNT(*), SUM(net_value) FROM raw_zrsd002")).fetchone()
print(f"\nraw_zrsd002 after cleanup:")
print(f"  Records: {total_raw[0]}")
print(f"  Net Value sum: {total_raw[1]:,.0f}")

# Re-transform to rebuild fact_billing
print("\n=== Re-transforming ===")
transformer = Transformer(db)
transformer.transform_zrsd002()

# Check fact_billing
fact_2026 = db.execute(text("""
    SELECT COUNT(*), SUM(net_value) 
    FROM fact_billing 
    WHERE billing_date >= '2026-01-01'
""")).fetchone()

print(f"\nfact_billing (2026 data):")
print(f"  Records: {fact_2026[0]}")
print(f"  Net Value sum: {fact_2026[1]:,.0f}")
print(f"\nExpected (from Excel): 6,632,510,377")
print(f"Match: {abs(fact_2026[1] - 6632510377) < 100}")
