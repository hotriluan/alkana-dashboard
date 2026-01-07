from src.db.connection import SessionLocal
from src.db.models import FactLeadTime, FactProduction, FactDelivery, FactBilling

db = SessionLocal()

try:
    # Get sample MTS order
    mts = db.query(FactLeadTime).filter(FactLeadTime.order_type == 'MTS').first()
    
    if mts:
        print(f"=== SAMPLE MTS ORDER ===")
        print(f"Order: {mts.order_number}")
        print(f"Batch: {mts.batch}")
        print(f"Material: {mts.material_code}")
        
        # Check if batch exists in FactProduction
        prod = db.query(FactProduction).filter(FactProduction.batch == mts.batch).first()
        if prod:
            print(f"\nFactProduction:")
            print(f"  Sales Order: {prod.sales_order}")
            print(f"  Is MTO: {prod.is_mto}")
            
        # Check if batch exists in FactDelivery
        delivery = db.query(FactDelivery).filter(FactDelivery.batch == mts.batch).first()
        if delivery:
            print(f"\nFactDelivery:")
            print(f"  Delivery Doc: {delivery.delivery_document}")
            print(f"  Sales Order: {delivery.sales_order}")
            
            # Check if this SO has channel in Billing
            if delivery.sales_order:
                billing = db.query(FactBilling).filter(FactBilling.so_number == delivery.sales_order).first()
                if billing:
                    print(f"\nFactBilling (via Delivery SO):")
                    print(f"  SO: {billing.so_number}")
                    print(f"  Channel: {billing.dist_channel}")
        
finally:
    db.close()
