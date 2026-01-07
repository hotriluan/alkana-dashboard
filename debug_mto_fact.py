from src.db.connection import SessionLocal
from src.db.models import FactLeadTime

def debug_mto_batch():
    print("=== DEBUGGING MTO BATCH 25L2474910 ===")
    db = SessionLocal()
    
    try:
        fact = db.query(FactLeadTime).filter(FactLeadTime.batch == "25L2474910").first()
        
        if fact:
            print(f"\nFactLeadTime Record:")
            print(f"  Batch: {fact.batch}")
            print(f"  Order Number: {fact.order_number}")
            print(f"  Order Type: '{fact.order_type}' (type: {type(fact.order_type)})")
            print(f"  Material Code: {fact.material_code}")
            print(f"  Plant Code: {fact.plant_code}")
            print(f"  Start Date: {fact.start_date}")
            print(f"  End Date: {fact.end_date}")
            print(f"  Preparation Days: {fact.preparation_days}")
            print(f"  Production Days: {fact.production_days}")
            print(f"  Transit Days: {fact.transit_days}")
            print(f"  Storage Days: {fact.storage_days}")
            print(f"  Lead Time Days: {fact.lead_time_days}")
            
            print(f"\nChecking conditions:")
            print(f"  fact.order_type == 'MTO': {fact.order_type == 'MTO'}")
            print(f"  fact.order_type in ['MTO', 'MTS']: {fact.order_type in ['MTO', 'MTS']}")
            print(f"  is_mto would be: {fact.order_type == 'MTO'}")
            print(f"  is_production would be: {fact.order_type in ['MTO', 'MTS']}")
            
        else:
            print("Batch not found in FactLeadTime")
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_mto_batch()
