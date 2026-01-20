import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))

print("=" * 80)
print("🔍 INVESTIGATING NULL DELIVERY_DATE PATTERN")
print("=" * 80)

# Get sample NULL records
query = """
SELECT delivery, line_item, actual_gi_date, raw_data 
FROM raw_zrsd004 
WHERE delivery_date IS NULL 
LIMIT 10
"""

df_null = pd.read_sql(query, conn)
print(f"\n❌ SAMPLE RECORDS WITH NULL DELIVERY_DATE:")
for idx, row in df_null.iterrows():
    print(f"  Delivery {row['delivery']}, Line {row['line_item']}: actual_gi_date = {row['actual_gi_date']}")
    
    # Check raw_data JSON for Delivery Date field
    raw_data = row['raw_data']
    if raw_data and 'Delivery Date' in raw_data:
        print(f"    raw_data['Delivery Date'] = {repr(raw_data['Delivery Date'])}")

# Get sample NON-NULL records
query2 = """
SELECT delivery, line_item, delivery_date, actual_gi_date, raw_data
FROM raw_zrsd004 
WHERE delivery_date IS NOT NULL 
LIMIT 10
"""

df_not_null = pd.read_sql(query2, conn)
print(f"\n✅ SAMPLE RECORDS WITH delivery_date:")
for idx, row in df_not_null.iterrows():
    print(f"  Delivery {row['delivery']}, Line {row['line_item']}: delivery_date = {row['delivery_date']}")
    
    # Check raw_data JSON for Delivery Date field
    raw_data = row['raw_data']
    if raw_data and 'Delivery Date' in raw_data:
        print(f"    raw_data['Delivery Date'] = {repr(raw_data['Delivery Date'])}")

# Check our specific deliveries in RAW_DATA JSON
print(f"\n🔎 CHECKING RAW_DATA JSON FOR SPECIFIC DELIVERIES:")
for delivery_num in ['1910053734', '1910053733', '1910053732']:
    query3 = f"""
    SELECT delivery, line_item, delivery_date, raw_data->>'Delivery Date' as raw_delivery_date
    FROM raw_zrsd004
    WHERE delivery = '{delivery_num}'
    ORDER BY line_item
    """
    df_specific = pd.read_sql(query3, conn)
    if len(df_specific) > 0:
        print(f"\n  Delivery {delivery_num}:")
        for idx, row in df_specific.iterrows():
            print(f"    Line {row['line_item']}: delivery_date (column) = {row['delivery_date']}, raw_data['Delivery Date'] = {repr(row['raw_delivery_date'])}")

conn.close()
