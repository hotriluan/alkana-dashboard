#!/usr/bin/env python3
"""Check Excel source data for missing delivery dates"""
import pandas as pd

# Read Excel
df = pd.read_excel('c:/dev/alkana-dashboard/demodata/zrsd004.xlsx', 
                   header=None, skiprows=1, dtype=str)

# Assign column names
df.columns = ['Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference', 
              'Req. Type', 'Delivery Type', 'Shipping Point', 'Sloc', 
              'Sales Office', 'Dist. Channel', 'Cust. Group', 'Sold-to Party',
              'Ship-to Party', 'Name of Ship-to', 'City of Ship-to', 
              'Regional Stru. Grp.', 'Transportation Zone', 'Salesman ID',
              'Salesman Name', 'Material', 'Description', 'Delivery Qty', 
              'Tonase', 'Tonase Unit', 'Actual Delivery Qty', 'Sales Unit',
              'Net Weight', 'Weight Unit', 'Volume', 'Volume Unit', 
              'Created By', 'Product Hierarchy', 'Line Item', 
              'Total Movement Goods Stat'][:len(df.columns)]

# Check specific deliveries
target_deliveries = ['1910053734', '1910053733', '1910053732', '1960001173']

print('=' * 70)
print('EXCEL FILE INVESTIGATION')
print('=' * 70)

for delivery in target_deliveries:
    records = df[df['Delivery'] == delivery]
    print(f'\n📦 Delivery: {delivery}')
    print(f'  Records found: {len(records)}')
    if len(records) > 0:
        for idx, row in records.head(3).iterrows():
            delivery_date = row['Delivery Date']
            actual_date = row['Actual GI Date']
            line_item = row['Line Item']
            print(f'    Line {line_item}: Delivery Date = "{delivery_date}", Actual = "{actual_date}"')

# Summary statistics
print('\n' + '=' * 70)
print('SUMMARY STATISTICS')
print('=' * 70)
total = len(df)
has_delivery_date = df['Delivery Date'].notna().sum()
missing_delivery_date = total - has_delivery_date

print(f'Total records: {total:,}')
print(f'With Delivery Date: {has_delivery_date:,} ({has_delivery_date/total*100:.1f}%)')
print(f'Missing Delivery Date: {missing_delivery_date:,} ({missing_delivery_date/total*100:.1f}%)')
