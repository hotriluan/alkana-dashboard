"""
Comprehensive analysis of batch 25L2492010 stuck hours calculation

This script will:
1. Check COOISPI data (production completion)
2. Check MB51 movements (all movement types)
3. Analyze the stuck hours calculation logic
4. Find the root cause of 207.3 hours
"""

import pandas as pd
from datetime import datetime

print("=" * 100)
print("COMPREHENSIVE ANALYSIS: BATCH 25L2492010 - STUCK HOURS CALCULATION")
print("=" * 100)

# Load COOISPI
cooispi_df = pd.read_excel('demodata/cooispi.XLSX')
batch_cooispi = cooispi_df[cooispi_df['Batch'] == '25L2492010']

print("\n1. COOISPI (PRODUCTION ORDER DATA)")
print("-" * 100)
if not batch_cooispi.empty:
    for col in batch_cooispi.columns:
        val = batch_cooispi[col].values[0]
        print(f"  {col}: {val}")
    
    actual_finish = pd.to_datetime(batch_cooispi['Actual finish date'].values[0])
    print(f"\n  Actual finish date (parsed): {actual_finish}")
else:
    print("  ✗ Batch not found in COOISPI!")
    actual_finish = None

# Load MB51
mb51_df = pd.read_excel('demodata/mb51.XLSX')
batch_mb51 = mb51_df[mb51_df['Batch'] == '25L2492010'].copy()

print("\n2. MB51 (MATERIAL MOVEMENTS)")
print("-" * 100)
if not batch_mb51.empty:
    batch_mb51['Posting Date'] = pd.to_datetime(batch_mb51['Posting Date'])
    batch_mb51_sorted = batch_mb51.sort_values('Posting Date')
    
    print(f"  Found {len(batch_mb51_sorted)} movement records:")
    print()
    for idx, row in batch_mb51_sorted.iterrows():
        print(f"  Movement {idx}:")
        print(f"    Posting Date: {row['Posting Date']}")
        print(f"    Movement Type: {row['Movement Type']}")
        print(f"    Plant: {row['Plant']}")
        print(f"    Storage Location: {row['Storage Location']}")
        print(f"    Material: {row['Material']}")
        print(f"    Quantity: {row.get('Quantity', 'N/A')}")
        print()
else:
    print("  ✗ No movements found for this batch!")

# Analyze MVT 101 at Plant 1401
print("\n3. MVT 101 ANALYSIS (Goods Receipt at DC)")
print("-" * 100)
mvt_101_1401 = batch_mb51[(batch_mb51['Movement Type'] == 101) & (batch_mb51['Plant'] == 1401)]
if not mvt_101_1401.empty:
    mvt_101_date = mvt_101_1401['Posting Date'].values[0]
    mvt_101_date_parsed = pd.to_datetime(mvt_101_date)
    print(f"  MVT 101 at Plant 1401:")
    print(f"    Posting Date: {mvt_101_date_parsed}")
    print(f"    Material: {mvt_101_1401['Material'].values[0]}")
else:
    print("  ✗ No MVT 101 at Plant 1401!")
    mvt_101_date_parsed = None

# Analyze MVT 601 at Plant 1401
print("\n4. MVT 601 ANALYSIS (Goods Issue from DC)")
print("-" * 100)
mvt_601_1401 = batch_mb51[(batch_mb51['Movement Type'] == 601) & (batch_mb51['Plant'] == 1401)]
if not mvt_601_1401.empty:
    mvt_601_date = mvt_601_1401['Posting Date'].values[0]
    mvt_601_date_parsed = pd.to_datetime(mvt_601_date)
    print(f"  MVT 601 at Plant 1401:")
    print(f"    Posting Date: {mvt_601_date_parsed}")
    print(f"    Material: {mvt_601_1401['Material'].values[0]}")
else:
    print("  ✗ No MVT 601 at Plant 1401 - STUCK IN TRANSIT!")
    mvt_601_date_parsed = None

# Calculate stuck hours based on alert logic
print("\n5. STUCK HOURS CALCULATION (Based on Alert Logic)")
print("-" * 100)
print("  Alert Logic:")
print("    - Receipt Date: MVT 101 posting date at Plant 1401")
print("    - Issue Date: MVT 601 posting date at Plant 1401")
print("    - Stuck Hours: Current Time - Receipt Date (if no issue)")
print("    - OR: Issue Date - Receipt Date (if issued)")
print()

if mvt_101_date_parsed is not None:
    current_time = datetime.now()
    
    if mvt_601_date_parsed is None:
        # Still stuck - calculate from current time
        stuck_hours = (current_time - mvt_101_date_parsed).total_seconds() / 3600
        print(f"  STATUS: STUCK IN TRANSIT (No MVT 601)")
        print(f"    Receipt Date (MVT 101): {mvt_101_date_parsed}")
        print(f"    Current Time: {current_time}")
        print(f"    Stuck Hours: {stuck_hours:.1f} hours")
    else:
        # Was stuck - calculate transit time
        transit_hours = (mvt_601_date_parsed - mvt_101_date_parsed).total_seconds() / 3600
        print(f"  STATUS: DELAYED TRANSIT (Has MVT 601)")
        print(f"    Receipt Date (MVT 101): {mvt_101_date_parsed}")
        print(f"    Issue Date (MVT 601): {mvt_601_date_parsed}")
        print(f"    Transit Hours: {transit_hours:.1f} hours")

# Compare with COOISPI
print("\n6. COMPARISON WITH COOISPI")
print("-" * 100)
if actual_finish is not None and mvt_101_date_parsed is not None:
    time_diff = mvt_101_date_parsed - actual_finish
    hours_diff = time_diff.total_seconds() / 3600
    
    print(f"  Production Actual Finish (COOISPI): {actual_finish}")
    print(f"  Goods Receipt at DC (MVT 101): {mvt_101_date_parsed}")
    print(f"  Time from Production to DC Receipt: {hours_diff:.1f} hours")
    print()
    print(f"  NOTE: This is NOT the stuck hours calculation!")
    print(f"        Stuck hours = time AFTER receipt at DC (MVT 101)")
    print(f"        until issue from DC (MVT 601) or current time")

# Check if 207.3 hours matches
print("\n7. ROOT CAUSE ANALYSIS")
print("-" * 100)
if mvt_101_date_parsed is not None:
    current_time = datetime.now()
    calculated_stuck = (current_time - mvt_101_date_parsed).total_seconds() / 3600
    
    print(f"  Expected stuck hours (from screenshot): 207.3 hours")
    print(f"  Calculated stuck hours (current): {calculated_stuck:.1f} hours")
    print()
    
    # Try to reverse engineer the detection time
    expected_stuck_hours = 207.3
    detection_time = mvt_101_date_parsed + pd.Timedelta(hours=expected_stuck_hours)
    print(f"  If stuck hours = 207.3, then:")
    print(f"    Detection Time = {detection_time}")
    print(f"    (Receipt Date + 207.3 hours)")
    print()
    
    # Check if this makes sense
    print(f"  Timeline:")
    print(f"    1. Production finished (COOISPI): {actual_finish}")
    print(f"    2. Goods received at DC (MVT 101): {mvt_101_date_parsed}")
    print(f"    3. Alert detected at: {detection_time} (estimated)")
    print(f"    4. Current time: {current_time}")

print("\n" + "=" * 100)
