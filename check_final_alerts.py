from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check batch 25L2502310
result = db.execute(text("""
    SELECT batch, stuck_hours, severity, message, detected_at
    FROM fact_alerts 
    WHERE batch = '25L2502310'
""")).fetchall()

print("Alert for batch 25L2502310:")
if result:
    for r in result:
        print(f"\nBatch: {r[0]}")
        print(f"Stuck Hours: {r[1]}")
        print(f"Severity: {r[2]}")
        print(f"Message: {r[3]}")
        print(f"Detected At: {r[4]}")
else:
    print("NO ALERT (expected - transit time = 0 hours)")

# Check all DELAYED_TRANSIT alerts
print("\n" + "=" * 80)
print("All DELAYED_TRANSIT alerts:")
result2 = db.execute(text("""
    SELECT batch, stuck_hours, severity, message
    FROM fact_alerts 
    WHERE alert_type = 'DELAYED_TRANSIT'
    ORDER BY stuck_hours DESC
""")).fetchall()

if result2:
    for r in result2:
        print(f"\nBatch: {r[0]} | Hours: {r[1]} | Severity: {r[2]}")
        print(f"Message: {r[3]}")
else:
    print("NO DELAYED_TRANSIT alerts")

db.close()
