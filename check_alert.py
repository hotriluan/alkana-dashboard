from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Get alert for batch 25L2502310
result = db.execute(text("""
    SELECT batch, stuck_hours, severity, message, detected_at
    FROM fact_alerts 
    WHERE batch = '25L2502310'
""")).fetchall()

print("Alert for batch 25L2502310:")
if result:
    for r in result:
        print(f"Batch: {r[0]}")
        print(f"Stuck Hours: {r[1]}")
        print(f"Severity: {r[2]}")
        print(f"Message: {r[3]}")
        print(f"Detected At: {r[4]}")
else:
    print("No alert found")

db.close()
