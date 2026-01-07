from src.db.connection import SessionLocal
from src.db.models import FactProduction

def debug_production_record():
    print("=== DEBUGGING PRODUCTION RECORD FOR 25L2460910 ===")
    db = SessionLocal()
    
    try:
        prod = db.query(FactProduction).filter(FactProduction.batch == "25L2460910").first()
        
        if prod:
            print(f"\nFactProduction Record Found:")
            print(f"  Batch: {prod.batch}")
            print(f"  Order Number: {prod.order_number}")
            print(f"  Sales Order: {prod.sales_order}")
            print(f"  MRP Controller: {prod.mrp_controller}")
            print(f"  Is MTO: {prod.is_mto}")
            print(f"  Release Date: {prod.release_date}")
            print(f"  Actual Finish Date: {prod.actual_finish_date}")
            print(f"  Actual Start Date: {getattr(prod, 'actual_start_date', 'N/A')}")
            
            print(f"\nWhy not processed:")
            if not prod.actual_finish_date:
                print(f"  [X] Missing actual_finish_date - SKIPPED by transform_lead_time()")
                print(f"  -> This is why it's classified as PURCHASE instead of MTO")
            else:
                print(f"  [OK] Has actual_finish_date - should be processed")
                
        else:
            print("❌ NOT FOUND in FactProduction")
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_production_record()
