"""Analyze raw_zrsd002 data distribution by date"""
from src.db.connection import get_db
from sqlalchemy import text

db = next(get_db())

print("=== raw_zrsd002 by billing_date ===")
result = db.execute(text("""
    SELECT billing_date, 
           COUNT(*) as records,
           SUM(net_value) as total_net_value
    FROM raw_zrsd002
    GROUP BY billing_date
    ORDER BY billing_date DESC
    LIMIT 20
""")).fetchall()

for row in result:
    net_val = row[2] if row[2] else 0
    print(f"{row[0]}: {row[1]:4d} records, Net Value: {net_val:,.0f}")

print("\n=== fact_billing by billing_date ===")
result2 = db.execute(text("""
    SELECT billing_date, 
           COUNT(*) as records,
           SUM(net_value) as total_net_value
    FROM fact_billing
    GROUP BY billing_date
    ORDER BY billing_date DESC
    LIMIT 20
""")).fetchall()

for row in result2:
    net_val = row[2] if row[2] else 0
    print(f"{row[0]}: {row[1]:4d} records, Net Value: {net_val:,.0f}")

# Check total records
total_raw = db.execute(text("SELECT COUNT(*) FROM raw_zrsd002")).scalar()
total_fact = db.execute(text("SELECT COUNT(*) FROM fact_billing")).scalar()
print(f"\nTotal: raw={total_raw}, fact={total_fact}")

# Dashboard shows only 2026 data
print("\n=== Dashboard shows 2026 data only ===")
result3 = db.execute(text("""
    SELECT MIN(billing_date), MAX(billing_date), 
           COUNT(*), SUM(net_value)
    FROM fact_billing
    WHERE billing_date >= '2026-01-01'
""")).fetchone()
print(f"2026 data: {result3[2]} records from {result3[0]} to {result3[1]}")
print(f"Net Value sum: {result3[3]:,.0f}")
print(f"Dashboard shows: 4,643,272,273")
print(f"Match: {abs(result3[3] - 4643272273) < 100}")
