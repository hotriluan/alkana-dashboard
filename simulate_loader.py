import pandas as pd
from pathlib import Path

file_path = Path('demodata/zrsd004.XLSX')

# Read exactly like the loader does
df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)

# Assign column names
df.columns = [
    'Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference',
    'Req. Type', 'Delivery Type', 'Shipping Point', 'Sloc',
    'Sales Office', 'Dist. Channel', 'Cust. Group', 'Sold-to Party',
    'Ship-to Party', 'Name of Ship-to', 'City of Ship-to',
    'Regional Stru. Grp.', 'Transportation Zone', 'Salesman ID',
    'Salesman Name', 'Material', 'Description', 'Delivery Qty',
    'Tonase', 'Tonase Unit', 'Actual Delivery Qty', 'Sales Unit',
    'Net Weight', 'Weight Unit', 'Volume', 'Volume Unit',
    'Created By', 'Product Hierarchy', 'Line Item',
    'Total Movement Goods Stat'
][:len(df.columns)]

print("=" * 80)
print("🔍 TESTING LOADER LOGIC - EXACT SIMULATION")
print("=" * 80)

# Test safe_datetime function
def safe_datetime(val):
    """Safely convert value to datetime"""
    if pd.isna(val):
        return None
    try:
        if isinstance(val, datetime):
            return val
        result = pd.to_datetime(val)
        return result
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return None

from datetime import datetime

# Find our specific deliveries
for delivery_num in ['1910053734', '1910053733', '1910053732']:
    print(f"\n🔎 Delivery: {delivery_num}")
    matches = df[df['Delivery'].astype(str).str.strip() == delivery_num]
    
    if len(matches) > 0:
        print(f"  Found {len(matches)} records")
        for idx, row in matches.iterrows():
            delivery_date_val = row.get('Delivery Date')
            line_item_val = row.get('Line Item')
            
            print(f"\n  Row {idx + 2}, Line {line_item_val}:")
            print(f"    raw value: {repr(delivery_date_val)} (type: {type(delivery_date_val).__name__})")
            print(f"    pd.isna(): {pd.isna(delivery_date_val)}")
            
            # Test safe_datetime
            parsed_date = safe_datetime(delivery_date_val)
            print(f"    safe_datetime() result: {parsed_date}")
    else:
        print(f"  ❌ NOT FOUND")
