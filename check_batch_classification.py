from src.db.connection import SessionLocal
from src.db.models import FactProduction, FactLeadTime

def check_batch_classification():
    print("=== CHECKING BATCH 25L2460910 CLASSIFICATION ===")
    db = SessionLocal()
    
    try:
        # Check FactProduction
        prod = db.query(FactProduction).filter(FactProduction.batch == "25L2460910").first()
        
        if prod:
            print(f"\nFactProduction Record:")
            print(f"  Batch: {prod.batch}")
            print(f"  Order Number: {prod.order_number}")
            print(f"  Sales Order: {prod.sales_order}")
            print(f"  MRP Controller: {prod.mrp_controller}")
            print(f"  Is MTO (current): {prod.is_mto}")
            print(f"\nMTO Classification Check:")
            print(f"  Has Sales Order: {prod.sales_order is not None and str(prod.sales_order).strip() != ''}")
            print(f"  Is P01: {prod.mrp_controller == 'P01'}")
            print(f"  Should be MTO: {prod.sales_order is not None and str(prod.sales_order).strip() != '' and prod.mrp_controller == 'P01'}")
        else:
            print("Not found in FactProduction")
            
        # Check FactLeadTime
        lead = db.query(FactLeadTime).filter(FactLeadTime.batch == "25L2460910").first()
        
        if lead:
            print(f"\nFactLeadTime Record:")
            print(f"  Order Type: {lead.order_type}")
            print(f"  Order Number: {lead.order_number}")
            print(f"  Prep Days: {lead.preparation_days}")
            print(f"  Prod Days: {lead.production_days}")
        else:
            print("\nNot found in FactLeadTime")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_batch_classification()
