"""
Debug batch 25L2502310 - why 144 hours when both dates are 11/12/2025?
"""
import pandas as pd
from datetime import datetime

print("=" * 80)
print("DEBUG: Batch 25L2502310")
print("=" * 80)

# Load data
cooispi = pd.read_excel('demodata/cooispi.XLSX')
mb51 = pd.read_excel('demodata/mb51.XLSX')

batch = '25L2502310'

# Check COOISPI
print("\n1. COOISPI Data:")
c = cooispi[cooispi['Batch'] == batch]
if not c.empty:
    print(f"   Batch: {c['Batch'].values[0]}")
    print(f"   Actual finish date: {c['Actual finish date'].values[0]}")
    print(f"   Material: {c['Material Number'].values[0]}")
    print(f"   MRP Controller: {c['MRP controller'].values[0]}")
    
    actual_finish = pd.to_datetime(c['Actual finish date'].values[0])
    print(f"   Parsed datetime: {actual_finish}")
else:
    print("   NOT FOUND in COOISPI")

# Check MB51 - all movements
print("\n2. MB51 - All Movements:")
m = mb51[mb51['Batch'] == batch].copy()
if not m.empty:
    m['Posting Date'] = pd.to_datetime(m['Posting Date'])
    m = m.sort_values('Posting Date')
    
    print(f"   Found {len(m)} movements:")
    for _, row in m.iterrows():
        mvt = int(row['Movement Type']) if pd.notna(row['Movement Type']) else 0
        print(f"     {row['Posting Date']} | MVT {mvt:3d} | Plant {row['Plant']} | SLoc {row['Storage Location']}")
else:
    print("   NOT FOUND in MB51")

# Check MVT 101 at Plant 1401 specifically
print("\n3. MVT 101 at Plant 1401:")
mvt_101 = mb51[(mb51['Batch'] == batch) & (mb51['Movement Type'] == 101) & (mb51['Plant'] == 1401)]
if not mvt_101.empty:
    posting_date = pd.to_datetime(mvt_101['Posting Date'].values[0])
    print(f"   Posting Date: {posting_date}")
    print(f"   Material: {mvt_101['Material'].values[0]}")
else:
    print("   NOT FOUND")

# Calculate expected transit time
print("\n4. Expected Transit Time Calculation:")
if not c.empty and not mvt_101.empty:
    actual_finish = pd.to_datetime(c['Actual finish date'].values[0])
    posting_date = pd.to_datetime(mvt_101['Posting Date'].values[0])
    
    print(f"   COOISPI Actual finish: {actual_finish}")
    print(f"   MB51 MVT 101 @ 1401: {posting_date}")
    
    transit_hours = (posting_date - actual_finish).total_seconds() / 3600
    print(f"   Transit hours: {transit_hours:.1f}")
    
    if transit_hours == 0:
        print("   ✓ Expected: 0 hours (same day)")
    else:
        print(f"   ✗ Unexpected: {transit_hours:.1f} hours")

# Check database alert
print("\n5. Database Alert:")
from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text("""
    SELECT batch, stuck_hours, severity, message, detected_at
    FROM fact_alerts 
    WHERE batch = :batch
"""), {"batch": batch}).fetchall()

if result:
    for r in result:
        print(f"   Batch: {r[0]}")
        print(f"   Stuck Hours: {r[1]}")
        print(f"   Severity: {r[2]}")
        print(f"   Message: {r[3]}")
        print(f"   Detected At: {r[4]}")
else:
    print("   No alert found in database")

db.close()

print("\n" + "=" * 80)
