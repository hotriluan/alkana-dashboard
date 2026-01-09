"""Reload zrsd002.xlsx with fixed loader"""
import sys
sys.path.insert(0, '.')

from src.etl.loaders import Zrsd002Loader
from src.db.connection import get_db
from sqlalchemy import text
from src.etl.transform import Transformer

db = next(get_db())

# Step 1: Delete 2026 data from raw_zrsd002 to avoid duplicates
print("=== Step 1: Clean 2026 data ===")
deleted = db.execute(text("""
    DELETE FROM raw_zrsd002
    WHERE billing_date >= '2026-01-01' AND billing_date <= '2026-01-08'
""")).rowcount
db.commit()
print(f"✓ Deleted {deleted} existing 2026 records")

# Step 2: Reload with fixed loader
print("\n=== Step 2: Reload zrsd002.xlsx ===")
loader = Zrsd002Loader(db, mode='insert')
stats = loader.load()
print(f"Loaded: {stats['loaded']}, Errors: {stats['errors']}")

# Step 3: Verify
result = db.execute(text("""
    SELECT COUNT(*), SUM(net_value)
    FROM raw_zrsd002
    WHERE billing_date >= '2026-01-01' AND billing_date <= '2026-01-08'
""")).fetchone()
print(f"\n✓ raw_zrsd002 (2026): {result[0]} records, Net Value: {result[1]:,.0f}")

# Step 4: Transform to fact_billing
print("\n=== Step 3: Transform ===")
transformer = Transformer(db)
transformer.transform_zrsd002()

# Step 5: Check fact_billing
fact_result = db.execute(text("""
    SELECT COUNT(*), SUM(net_value)
    FROM fact_billing
    WHERE billing_date >= '2026-01-01' AND billing_date <= '2026-01-08'
""")).fetchone()
print(f"\n✓ fact_billing (2026): {fact_result[0]} records, Net Value: {fact_result[1]:,.0f}")
print(f"Expected from Excel: 534 records, 6,632,510,377")
print(f"Match: {result[0] == 534 and abs(result[1] - 6632510377) < 100}")
