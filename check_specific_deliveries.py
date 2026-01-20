import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("🔎 CHECKING SPECIFIC DELIVERIES:")

for delivery_num in ['1910053734', '1910053733', '1910053732']:
    # Check raw_zrsd004
    cur.execute(f"""
        SELECT line_item, delivery_date, actual_gi_date
        FROM raw_zrsd004
        WHERE delivery = '{delivery_num}'
        ORDER BY line_item
    """)
    raw_records = cur.fetchall()
    
    # Check fact_delivery
    cur.execute(f"""
        SELECT line_item, delivery_date, actual_gi_date
        FROM fact_delivery
        WHERE delivery = '{delivery_num}'
        ORDER BY line_item
    """)
    fact_records = cur.fetchall()
    
    print(f"\n📦 Delivery {delivery_num}:")
    print(f"  RAW_ZRSD004: {len(raw_records)} records")
    for line_item, delivery_date, actual_gi_date in raw_records:
        status = "✅" if delivery_date else "❌"
        print(f"    {status} Line {line_item}: delivery_date = {delivery_date}")
    
    print(f"  FACT_DELIVERY: {len(fact_records)} records")
    for line_item, delivery_date, actual_gi_date in fact_records:
        status = "✅" if delivery_date else "❌"
        print(f"    {status} Line {line_item}: delivery_date = {delivery_date}")

cur.close()
conn.close()
