from src.db.connection import SessionLocal
from src.db.models import FactLeadTime

def check_mto_batch():
    print("=== FINDING MTO BATCH WITH PREPARATION TIME ===")
    db = SessionLocal()
    
    try:
        # Find an MTO batch with preparation time
        mto_batch = db.query(FactLeadTime)\
            .filter(FactLeadTime.order_type == 'MTO')\
            .filter(FactLeadTime.preparation_days > 0)\
            .first()
            
        if mto_batch:
            print(f"\nFound MTO Batch: {mto_batch.batch}")
            print(f"Order Number: {mto_batch.order_number}")
            print(f"Order Type: {mto_batch.order_type}")
            print(f"Preparation Days: {mto_batch.preparation_days}")
            print(f"Production Days: {mto_batch.production_days}")
            print(f"Storage Days: {mto_batch.storage_days}")
            print(f"Total Lead Time: {mto_batch.lead_time_days}")
        else:
            print("No MTO batch with preparation time found")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_mto_batch()
