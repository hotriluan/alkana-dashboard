"""
Re-run transform to process all raw_zrsd002 data
"""
from src.etl.transform import Transformer
from src.db.connection import get_db

print("Re-running transform_zrsd002 to process all raw data...\n")

db = next(get_db())
transformer = Transformer(db)

# Clear existing fact_billing data first
print("Clearing existing fact_billing data...")
from src.db.models import FactBilling
deleted = db.query(FactBilling).delete()
db.commit()
print(f"  ✓ Deleted {deleted} existing records\n")

# Transform all raw data
transformer.transform_zrsd002()

db.close()

print("\nTransform completed! Verifying...")

# Verify
db2 = next(get_db())
from sqlalchemy import text
result = db2.execute(text("""
    SELECT 
        TO_CHAR(billing_date, 'YYYY-MM') as month,
        COUNT(*) as rows,
        COUNT(DISTINCT billing_document) as docs,
        SUM(net_value) as revenue
    FROM fact_billing
    GROUP BY month
    ORDER BY month
"""))

print("\nfact_billing data by month:")
total_revenue = 0
for row in result:
    print(f"  {row[0]}: {row[1]} rows, {row[2]} docs, {row[3]:,.0f} revenue")
    total_revenue += row[3]

print(f"\nTotal Revenue (all 2025): {total_revenue:,.2f}")
db2.close()
