"""Verify V2 data and test API logic"""
from src.db.connection import get_db
from sqlalchemy import text
from datetime import date, timedelta

db = next(get_db())

# Check data in fact_production_performance_v2
print("=== Checking fact_production_performance_v2 ===")
result = db.execute(text("""
    SELECT COUNT(*),
           MIN(posting_date),
           MAX(posting_date),
           COUNT(DISTINCT process_order_id)
    FROM fact_production_performance_v2
""")).fetchone()

print(f"Total records: {result[0]}")
print(f"Date range: {result[1]} to {result[2]}")
print(f"Unique orders: {result[3]}")

# Test default date range (last 30 days)
end_date = date.today()
start_date = end_date - timedelta(days=30)
print(f"\n=== Testing default date range ===")
print(f"Start: {start_date}, End: {end_date}")

result2 = db.execute(text("""
    SELECT COUNT(*)
    FROM fact_production_performance_v2
    WHERE posting_date >= :start_date 
      AND posting_date <= :end_date
"""), {"start_date": start_date, "end_date": end_date}).scalar()

print(f"Records in range: {result2}")

if result2 == 0:
    print("\n⚠ No data in default 30-day range!")
    print(f"  Latest data: {result[2]}")
    print(f"  Need to adjust default range or use explicit dates")
