from src.db.connection import SessionLocal
from src.db.models import FactLeadTime, FactProduction

def find_real_mto():
    print("=== FINDING REAL MTO BATCH ===")
    db = SessionLocal()
    
    try:
        # Find MTO from FactProduction first
        mto_prod = db.query(FactProduction)\
            .filter(FactProduction.is_mto == True)\
            .filter(FactProduction.batch != None)\
            .first()
            
        if mto_prod:
            print(f"\nFound MTO Production Order:")
            print(f"  Batch: {mto_prod.batch}")
            print(f"  Order Number: {mto_prod.order_number}")
            print(f"  Is MTO: {mto_prod.is_mto}")
            
            # Check if it exists in FactLeadTime
            lead_time = db.query(FactLeadTime)\
                .filter(FactLeadTime.batch == mto_prod.batch)\
                .first()
                
            if lead_time:
                print(f"\nFactLeadTime Record:")
                print(f"  Order Type: {lead_time.order_type}")
                print(f"  Prep Days: {lead_time.preparation_days}")
                print(f"  Prod Days: {lead_time.production_days}")
                print(f"  Storage Days: {lead_time.storage_days}")
            else:
                print("\n  NOT FOUND in FactLeadTime")
        else:
            print("No MTO production order found")
            
    finally:
        db.close()

if __name__ == "__main__":
    find_real_mto()
