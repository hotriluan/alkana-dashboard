from src.db.connection import SessionLocal
from src.db.models import FactLeadTime
import json
from sqlalchemy import desc

def verify():
    print("=== VERIFYING LEAD TIME DATA QUALITY ===")
    db = SessionLocal()
    try:
        # Check top 5 orders
        orders = db.query(FactLeadTime).order_by(desc(FactLeadTime.id)).limit(5).all()
        
        # Check top 5 orders WITH preparation time (MTO Backtracking)
        orders_with_prep = db.query(FactLeadTime)\
            .filter(FactLeadTime.preparation_days > 0)\
            .limit(5).all()
            
        print(f"\nFound {len(orders_with_prep)} orders with Preparation Time > 0:")
        for o in orders_with_prep:
             print(f"- Order: {o.order_number} ({o.order_type})")
             print(f"  Batch: {o.batch}")
             print(f"  Stages: Prep={o.preparation_days}, Prod={o.production_days}, Transit={o.transit_days}, Storage={o.storage_days}")
             print(f"  Total: {o.lead_time_days} days")
             print("-" * 40)
             
        # Count total with prep
        count_prep = db.query(FactLeadTime).filter(FactLeadTime.preparation_days > 0).count()
        print(f"\nTotal records with valid Preparation Time: {count_prep}")
            
        # Check counts
        count_mto = db.query(FactLeadTime).filter(FactLeadTime.order_type == 'MTO').count()
        count_mts = db.query(FactLeadTime).filter(FactLeadTime.order_type == 'MTS').count()
        count_purch = db.query(FactLeadTime).filter(FactLeadTime.order_type == 'PURCHASE').count()
        
        print(f"\nCounts: MTO={count_mto}, MTS={count_mts}, PURCHASE={count_purch}")
        
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify()
