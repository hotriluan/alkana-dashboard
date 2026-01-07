"""
Simple explanation of stuck hours calculation logic for batch 25L2492010
"""

import pandas as pd
from datetime import datetime

print("STUCK HOURS CALCULATION LOGIC")
print("=" * 80)

# Load data
cooispi_df = pd.read_excel('demodata/cooispi.XLSX')
mb51_df = pd.read_excel('demodata/mb51.XLSX')

# Get batch data
batch = '25L2492010'
cooispi_data = cooispi_df[cooispi_df['Batch'] == batch]
mb51_data = mb51_df[mb51_df['Batch'] == batch].copy()
mb51_data['Posting Date'] = pd.to_datetime(mb51_data['Posting Date'])
mb51_data = mb51_data.sort_values('Posting Date')

# Show COOISPI
print("\n1. COOISPI - Production Order Data:")
if not cooispi_data.empty:
    actual_finish = pd.to_datetime(cooispi_data['Actual finish date'].values[0])
    print(f"   Actual finish date: {actual_finish}")
    print(f"   (This is when PRODUCTION finished at factory)")

# Show MB51 movements
print("\n2. MB51 - Material Movements:")
for _, row in mb51_data.iterrows():
    print(f"   {row['Posting Date']} | MVT {row['Movement Type']} | Plant {row['Plant']} | SLoc {row['Storage Location']}")

# Explain logic
print("\n3. STUCK HOURS CALCULATION LOGIC:")
print("   The system calculates 'stuck hours' as:")
print("   ")
print("   FROM: MVT 101 posting date at Plant 1401 (goods RECEIVED at DC)")
print("   TO:   MVT 601 posting date at Plant 1401 (goods ISSUED from DC)")
print("   OR:   Current time (if no MVT 601 yet)")

# Get MVT 101 at 1401
mvt_101 = mb51_data[(mb51_data['Movement Type'] == 101) & (mb51_data['Plant'] == 1401)]
mvt_601 = mb51_data[(mb51_data['Movement Type'] == 601) & (mb51_data['Plant'] == 1401)]

print("\n4. FOR BATCH 25L2492010:")
if not mvt_101.empty:
    receipt_date = mvt_101['Posting Date'].values[0]
    receipt_dt = pd.to_datetime(receipt_date)
    print(f"   Receipt at DC (MVT 101): {receipt_dt}")
    
    if not mvt_601.empty:
        issue_date = mvt_601['Posting Date'].values[0]
        issue_dt = pd.to_datetime(issue_date)
        print(f"   Issue from DC (MVT 601): {issue_dt}")
        hours = (issue_dt - receipt_dt).total_seconds() / 3600
        print(f"   Stuck hours: {hours:.1f} hours (DELAYED_TRANSIT)")
    else:
        current = datetime.now()
        hours = (current - receipt_dt).total_seconds() / 3600
        print(f"   Issue from DC (MVT 601): NOT YET!")
        print(f"   Current time: {current}")
        print(f"   Stuck hours: {hours:.1f} hours (STUCK_IN_TRANSIT)")

print("\n5. KEY POINT:")
print("   Stuck hours DOES NOT use COOISPI Actual finish date!")
print("   It only uses MB51 movement dates (101 and 601) at Plant 1401")
print("   ")
print("   COOISPI Actual finish date = when production finished at factory")
print("   MVT 101 at Plant 1401 = when goods received at DC warehouse")
print("   MVT 601 at Plant 1401 = when goods issued from DC warehouse")

print("\n" + "=" * 80)
