"""
Truncate fact tables and re-transform from clean raw data
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import sys

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

session = Session()

print("\n" + "="*80)
print("  TRUNCATING FACT TABLES")
print("="*80 + "\n")

fact_tables = [
    'fact_production',
    'fact_inventory',
    'fact_purchase_order',
    'fact_billing',
    'fact_delivery',
    'fact_ar_aging',
    'fact_target',
    'fact_production_chain',
    'fact_mto_orders',
    'fact_alerts',
    'fact_lead_time'
]

for table in fact_tables:
    try:
        session.execute(text(f'TRUNCATE TABLE {table} RESTART IDENTITY CASCADE'))
        session.commit()
        print(f"  Truncated {table}")
    except Exception as e:
        session.rollback()
        print(f"  Error truncating {table}: {e}")

print("\n" + "="*80)
print("  RE-TRANSFORMING FROM RAW DATA")
print("="*80 + "\n")

sys.path.insert(0, 'src')
from src.etl.transform import Transformer

transformer = Transformer(session)
transformer.transform_all()

print("\n" + "="*80)
print("  VALIDATION")
print("="*80 + "\n")

result = session.execute(text("""
    SELECT 
        COUNT(*) as rows,
        COUNT(DISTINCT billing_document) as docs,
        SUM(net_value)/1000000000 as revenue_b,
        COUNT(DISTINCT customer_name) as customers
    FROM fact_billing
""")).fetchone()

print(f"FACT_BILLING:")
print(f"  Rows: {result[0]:,}")
print(f"  Documents: {result[1]:,}")
print(f"  Revenue: {result[2]:.2f}B VND")
print(f"  Customers: {result[3]:,}")

# Check for duplicates
dups = session.execute(text("""
    SELECT billing_document, billing_item, COUNT(*) as cnt
    FROM fact_billing
    GROUP BY billing_document, billing_item
    HAVING COUNT(*) > 1
    LIMIT 1
""")).fetchone()

if dups:
    print(f"\n  WARNING: Still has duplicates! Doc {dups[0]}, Item {dups[1]}: {dups[2]} times")
else:
    print(f"\n  OK: No duplicates found")

session.close()

print("\n" + "="*80)
print("  TRANSFORM COMPLETED!")
print("="*80)
