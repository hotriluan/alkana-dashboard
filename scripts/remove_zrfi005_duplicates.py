"""Remove duplicate ZRFI005 records for 2026-01-08"""
from src.db.connection import get_db
from sqlalchemy import text

db = next(get_db())

print("Removing duplicates from raw_zrfi005 for snapshot_date = 2026-01-08...")

# Keep only MIN(id) per business key (customer_name + snapshot_date)
result = db.execute(text("""
    DELETE FROM raw_zrfi005
    WHERE snapshot_date = '2026-01-08'
    AND id NOT IN (
        SELECT MIN(id)
        FROM raw_zrfi005
        WHERE snapshot_date = '2026-01-08'
        GROUP BY customer_name, dist_channel, cust_group, salesman_name, snapshot_date
    )
"""))

deleted = result.rowcount
db.commit()

print(f"  ✓ Deleted {deleted} duplicate raw records")

# Check remaining count
remaining = db.execute(text("""
    SELECT COUNT(*) FROM raw_zrfi005 WHERE snapshot_date = '2026-01-08'
""")).scalar()

print(f"  ✓ Remaining: {remaining} records for 2026-01-08")

# Re-transform to fix fact table
print("\nRe-transforming to fact_ar_aging...")
from src.etl.transform import Transformer

# Clear fact_ar_aging for this snapshot
db.execute(text("DELETE FROM fact_ar_aging WHERE snapshot_date = '2026-01-08'"))
db.commit()

# Re-transform
transformer = Transformer(db)
transformer.transform_zrfi005(target_date='2026-01-08')

# Verify
fact_count = db.execute(text("""
    SELECT COUNT(*) FROM fact_ar_aging WHERE snapshot_date = '2026-01-08'
""")).scalar()

print(f"  ✓ Fact table: {fact_count} records for 2026-01-08")

db.close()
print("\n✅ Cleanup complete!")
