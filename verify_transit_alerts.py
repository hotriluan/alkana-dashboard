"""
Verify transit time alerts after fix
"""
from src.db.connection import SessionLocal
from sqlalchemy import text
import pandas as pd

print("=" * 80)
print("VERIFICATION: Transit Time Alerts")
print("=" * 80)

db = SessionLocal()

# Check alert types
print("\n1. Alert Types Summary:")
result = db.execute(text("SELECT alert_type, COUNT(*) as count FROM fact_alerts GROUP BY alert_type")).fetchall()
for r in result:
    print(f"   {r[0]}: {r[1]} alerts")

# Check DELAYED_TRANSIT alerts
print("\n2. DELAYED_TRANSIT Alerts:")
result = db.execute(text("""
    SELECT batch, stuck_hours, severity, message 
    FROM fact_alerts 
    WHERE alert_type = 'DELAYED_TRANSIT' 
    ORDER BY stuck_hours DESC
""")).fetchall()

if result:
    for r in result:
        print(f"\n   Batch: {r[0]}")
        print(f"   Transit Hours: {r[1]}")
        print(f"   Severity: {r[2]}")
        print(f"   Message: {r[3]}")
else:
    print("   No DELAYED_TRANSIT alerts found")

# Check batch 25L2492010
print("\n3. Batch 25L2492010 Verification:")
result = db.execute(text("""
    SELECT batch, stuck_hours, alert_type, message 
    FROM fact_alerts 
    WHERE batch = '25L2492010'
""")).fetchall()

if result:
    for r in result:
        print(f"   Found alert: {r[2]}")
        print(f"   Transit Hours: {r[1]}")
        print(f"   Message: {r[3]}")
else:
    print("   No alert for batch 25L2492010")
    print("   Checking raw data...")
    
    # Load raw data
    cooispi = pd.read_excel('demodata/cooispi.XLSX')
    mb51 = pd.read_excel('demodata/mb51.XLSX')
    
    c = cooispi[cooispi['Batch'] == '25L2492010']
    m = mb51[(mb51['Batch'] == '25L2492010') & (mb51['Movement Type'] == 101) & (mb51['Plant'] == 1401)]
    
    if not c.empty and not m.empty:
        finish = pd.to_datetime(c['Actual finish date'].values[0])
        receipt = pd.to_datetime(m['Posting Date'].values[0])
        hours = (receipt - finish).total_seconds() / 3600
        
        print(f"   COOISPI Actual finish: {finish}")
        print(f"   MB51 MVT 101 @ 1401: {receipt}")
        print(f"   Transit hours: {hours:.1f}")
        print(f"   Threshold: 48 hours")
        
        if hours <= 48:
            print(f"   ✓ No alert expected (below threshold)")
        else:
            print(f"   ✗ Alert should exist (above threshold)")

db.close()

print("\n" + "=" * 80)
