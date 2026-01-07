"""
Deep debug for batch 25L2502310
Check actual dates with time components
"""
import pandas as pd
from datetime import datetime
from src.db.connection import SessionLocal
from src.db.models import FactProduction

print("=" * 80)
print("DEEP DEBUG: Batch 25L2502310")
print("=" * 80)

# Check FactProduction
db = SessionLocal()
prod = db.query(FactProduction).filter(FactProduction.batch == '25L2502310').first()

if prod:
    print("\n1. FactProduction (from database):")
    print(f"   Batch: {prod.batch}")
    print(f"   Actual finish date: {prod.actual_finish_date}")
    print(f"   Type: {type(prod.actual_finish_date)}")
    print(f"   MRP Controller: {prod.mrp_controller}")
    
    # Convert to datetime
    if isinstance(prod.actual_finish_date, datetime):
        finish_dt = prod.actual_finish_date
    else:
        finish_dt = datetime.combine(prod.actual_finish_date, datetime.min.time())
    
    print(f"   Converted to datetime: {finish_dt}")
else:
    print("\n1. NOT FOUND in FactProduction")
    finish_dt = None

db.close()

# Check MB51
print("\n2. MB51 (from Excel):")
mb51 = pd.read_excel('demodata/mb51.XLSX')
m = mb51[(mb51['Batch'] == '25L2502310') & (mb51['Movement Type'] == 101) & (mb51['Plant'] == 1401)]

if not m.empty:
    posting_date_raw = m['Posting Date'].values[0]
    print(f"   Raw posting date: {posting_date_raw}")
    print(f"   Type: {type(posting_date_raw)}")
    
    posting_dt = pd.to_datetime(posting_date_raw)
    print(f"   Converted to datetime: {posting_dt}")
else:
    print("   NOT FOUND")
    posting_dt = None

# Calculate transit time
if finish_dt and posting_dt:
    print("\n3. Transit Time Calculation:")
    print(f"   Production finish: {finish_dt}")
    print(f"   DC receipt (MVT 101): {posting_dt}")
    
    # Check if posting_dt is pandas Timestamp
    if hasattr(posting_dt, 'to_pydatetime'):
        posting_dt_py = posting_dt.to_pydatetime()
    else:
        posting_dt_py = posting_dt
    
    print(f"   Python datetime: {posting_dt_py}")
    
    transit_seconds = (posting_dt_py - finish_dt).total_seconds()
    transit_hours = transit_seconds / 3600
    
    print(f"   Transit seconds: {transit_seconds}")
    print(f"   Transit hours: {transit_hours:.1f}")
    
    if transit_hours == 144.0:
        print(f"\n   ✗ FOUND THE BUG! Transit time = 144 hours")
        print(f"   This means there's a 6-day difference")
        print(f"   Checking date components...")
        print(f"     Finish: {finish_dt.year}-{finish_dt.month:02d}-{finish_dt.day:02d} {finish_dt.hour:02d}:{finish_dt.minute:02d}")
        print(f"     Receipt: {posting_dt_py.year}-{posting_dt_py.month:02d}-{posting_dt_py.day:02d} {posting_dt_py.hour:02d}:{posting_dt_py.minute:02d}")

print("\n" + "=" * 80)
