from src.db.connection import SessionLocal
from src.db.models import FactP02P01Yield, FactAlert

db = SessionLocal()

try:
    print("=== P02→P01 YIELD DATA ===\n")
    
    # Count yields
    total_yields = db.query(FactP02P01Yield).count()
    print(f"Total P02→P01 pairs: {total_yields}")
    
    # Yield statistics
    from sqlalchemy import func
    
    stats = db.query(
        func.avg(FactP02P01Yield.yield_pct).label('avg_yield'),
        func.min(FactP02P01Yield.yield_pct).label('min_yield'),
        func.max(FactP02P01Yield.yield_pct).label('max_yield'),
        func.sum(FactP02P01Yield.loss_kg).label('total_loss')
    ).first()
    
    print(f"\nYield Statistics:")
    print(f"  Average Yield: {stats.avg_yield:.2f}%")
    print(f"  Min Yield: {stats.min_yield:.2f}%")
    print(f"  Max Yield: {stats.max_yield:.2f}%")
    print(f"  Total Loss: {stats.total_loss:.2f} KG")
    
    # Sample low yields
    print(f"\n=== TOP 10 LOWEST YIELDS ===")
    low_yields = db.query(FactP02P01Yield)\
        .order_by(FactP02P01Yield.yield_pct)\
        .limit(10).all()
    
    for y in low_yields:
        print(f"\nBatch: {y.p02_batch} → {y.p01_batch}")
        print(f"  P02: {y.p02_material_desc}")
        print(f"  P01: {y.p01_material_desc}")
        print(f"  Input: {y.p02_consumed_kg} KG")
        print(f"  Output: {y.p01_produced_kg} KG")
        print(f"  Yield: {y.yield_pct}%")
        print(f"  Loss: {y.loss_kg} KG")
    
    # Alert breakdown
    print(f"\n=== ALERT SUMMARY ===\n")
    
    alert_counts = db.query(
        FactAlert.alert_type,
        FactAlert.severity,
        func.count(FactAlert.id).label('count')
    ).group_by(FactAlert.alert_type, FactAlert.severity).all()
    
    total = 0
    for alert_type, severity, count in alert_counts:
        print(f"{alert_type} - {severity}: {count} alerts")
        total += count
    
    print(f"\nTotal: {total} alerts")
    
    # Low yield alerts specifically
    print(f"\n=== LOW YIELD ALERTS ===")
    low_yield_alerts = db.query(FactAlert)\
        .filter(FactAlert.alert_type == 'LOW_YIELD')\
        .order_by(FactAlert.yield_pct)\
        .limit(5).all()
    
    for alert in low_yield_alerts:
        print(f"\nBatch: {alert.batch}")
        print(f"  Material: {alert.material}")
        print(f"  Yield: {alert.yield_pct}%")
        print(f"  Severity: {alert.severity}")
        print(f"  Message: {alert.message}")
    
finally:
    db.close()
