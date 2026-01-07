"""
Debug script to analyze stuck hours calculation for batch 25L2492010

This script will:
1. Load COOISPI data to get Actual finish date
2. Load MB51 data to get posting date for MVT 101, Plant 1401
3. Calculate the time difference to understand the 207.3 hours
"""

import pandas as pd
from datetime import datetime

# Load data
print("=" * 80)
print("ANALYZING BATCH 25L2492010 - STUCK HOURS CALCULATION")
print("=" * 80)

# Load COOISPI
cooispi_df = pd.read_excel('demodata/cooispi.XLSX')
print("\n1. COOISPI DATA:")
print("-" * 80)
batch_cooispi = cooispi_df[cooispi_df['Batch'] == '25L2492010']
if not batch_cooispi.empty:
    print(f"Batch: {batch_cooispi['Batch'].values[0]}")
    print(f"Order: {batch_cooispi['Order'].values[0]}")
    print(f"Actual finish date: {batch_cooispi['Actual finish date'].values[0]}")
    print(f"Basic finish date: {batch_cooispi['Basic finish date'].values[0]}")
    actual_finish = pd.to_datetime(batch_cooispi['Actual finish date'].values[0])
    print(f"Actual finish date (parsed): {actual_finish}")
else:
    print("Batch not found in COOISPI!")

# Load MB51
mb51_df = pd.read_excel('demodata/mb51.XLSX')
print("\n2. MB51 DATA:")
print("-" * 80)
batch_mb51 = mb51_df[
    (mb51_df['Batch'] == '25L2492010') & 
    (mb51_df['Movement Type'] == 101) & 
    (mb51_df['Plant'] == 1401)
]
if not batch_mb51.empty:
    print(f"Found {len(batch_mb51)} records for MVT 101, Plant 1401")
    for idx, row in batch_mb51.iterrows():
        print(f"\nRecord {idx}:")
        print(f"  Posting Date: {row['Posting Date']}")
        print(f"  Movement Type: {row['Movement Type']}")
        print(f"  Plant: {row['Plant']}")
        print(f"  Material: {row['Material']}")
        print(f"  Batch: {row['Batch']}")
        posting_date = pd.to_datetime(row['Posting Date'])
        print(f"  Posting Date (parsed): {posting_date}")
else:
    print("No records found for MVT 101, Plant 1401!")

# Calculate stuck hours
print("\n3. STUCK HOURS CALCULATION:")
print("-" * 80)
if not batch_cooispi.empty and not batch_mb51.empty:
    actual_finish = pd.to_datetime(batch_cooispi['Actual finish date'].values[0])
    posting_date = pd.to_datetime(batch_mb51['Posting Date'].values[0])
    
    time_diff = posting_date - actual_finish
    hours_diff = time_diff.total_seconds() / 3600
    
    print(f"Actual finish date (COOISPI): {actual_finish}")
    print(f"Posting date (MB51 MVT 101): {posting_date}")
    print(f"Time difference: {time_diff}")
    print(f"Hours difference: {hours_diff:.1f} hours")
    
    if abs(hours_diff - 207.3) < 1:
        print(f"\n✓ MATCH! This explains the 207.3 hours stuck time.")
    else:
        print(f"\n✗ MISMATCH! Expected 207.3 hours but got {hours_diff:.1f} hours")
        print(f"   Difference: {abs(hours_diff - 207.3):.1f} hours")

# Check if there are other movement types for this batch
print("\n4. ALL MB51 MOVEMENTS FOR THIS BATCH:")
print("-" * 80)
all_batch_movements = mb51_df[mb51_df['Batch'] == '25L2492010'].sort_values('Posting Date')
if not all_batch_movements.empty:
    print(all_batch_movements[['Posting Date', 'Movement Type', 'Plant', 'Storage Location', 'Material', 'Batch']].to_string())
else:
    print("No movements found for this batch!")

print("\n" + "=" * 80)
