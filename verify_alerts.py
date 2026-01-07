from src.db.connection import SessionLocal
from src.db.models import FactAlert

db = SessionLocal()

try:
    # Get alert counts by type
    from sqlalchemy import func
    
    alert_counts = db.query(
        FactAlert.alert_type,
        FactAlert.severity,
        func.count(FactAlert.id).label('count')
    ).group_by(FactAlert.alert_type, FactAlert.severity).all()
    
    print("=== ALERT SUMMARY ===\n")
    
    total = 0
    for alert_type, severity, count in alert_counts:
        print(f"{alert_type} - {severity}: {count} alerts")
        total += count
    
    print(f"\nTotal: {total} alerts")
    
    # Sample low yield alerts
    print("\n=== SAMPLE LOW YIELD ALERTS ===")
    low_yield = db.query(FactAlert)\
        .filter(FactAlert.alert_type == 'LOW_YIELD')\
        .order_by(FactAlert.yield_pct)\
        .limit(10).all()
    
    for alert in low_yield:
        print(f"\nMaterial: {alert.material}")
        print(f"  Yield: {alert.yield_pct}%")
        print(f"  Severity: {alert.severity}")
        print(f"  Status: {alert.status}")
    
    # Sample stuck inventory alerts
    print("\n=== SAMPLE STUCK INVENTORY ALERTS ===")
    stuck = db.query(FactAlert)\
        .filter(FactAlert.alert_type.in_(['STUCK_IN_TRANSIT', 'DELAYED_TRANSIT']))\
        .order_by(FactAlert.stuck_hours.desc())\
        .limit(10).all()
    
    for alert in stuck:
        print(f"\nBatch: {alert.batch}")
        print(f"  Hours: {alert.stuck_hours}h")
        print(f"  Severity: {alert.severity}")
        print(f"  Plant: {alert.plant}")
        
finally:
    db.close()
