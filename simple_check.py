"""
Simple check: what's in COOISPI vs MB51 for batch 25L2502310
"""
import pandas as pd

cooispi = pd.read_excel('demodata/cooispi.XLSX')
mb51 = pd.read_excel('demodata/mb51.XLSX')

batch = '25L2502310'

print(f"Batch: {batch}\n")

# COOISPI
c = cooispi[cooispi['Batch'] == batch]
if not c.empty:
    print(f"COOISPI Actual finish date: {c['Actual finish date'].values[0]}")
else:
    print("NOT in COOISPI")

# MB51
m = mb51[(mb51['Batch'] == batch) & (mb51['Movement Type'] == 101) & (mb51['Plant'] == 1401)]
if not m.empty:
    print(f"MB51 MVT 101 @ 1401: {m['Posting Date'].values[0]}")
else:
    print("NOT in MB51")

# Calculate
if not c.empty and not m.empty:
    finish = pd.to_datetime(c['Actual finish date'].values[0])
    receipt = pd.to_datetime(m['Posting Date'].values[0])
    hours = (receipt - finish).total_seconds() / 3600
    print(f"\nTransit hours: {hours:.1f}")
    print(f"Days: {hours/24:.1f}")
