from src.db.connection import SessionLocal
from src.db.models import FactLeadTime, FactBilling, FactProduction
import json

db = SessionLocal()

try:
    # Check channel data in FactLeadTime
    total = db.query(FactLeadTime).count()
    with_channel = db.query(FactLeadTime).filter(FactLeadTime.channel_code.isnot(None)).count()
    
    print(f"=== FACT_LEAD_TIME CHANNEL DATA ===")
    print(f"Total Records: {total}")
    print(f"With Channel: {with_channel}")
    print(f"Without Channel: {total - with_channel}")
    
    # Sample SO from Production
    prod_sample = db.query(FactProduction.sales_order).filter(FactProduction.sales_order.isnot(None)).first()
    if prod_sample:
        print(f"\nSample Production SO: '{prod_sample[0]}'")
        
    # Sample SO from Billing
    bill_sample = db.query(FactBilling.so_number).filter(FactBilling.so_number.isnot(None)).first()
    if bill_sample:
        print(f"Sample Billing SO: '{bill_sample[0]}'")
        
    # Check if they match
    if prod_sample and bill_sample:
        prod_so = str(prod_sample[0]).strip()
        bill_so = str(bill_sample[0]).strip()
        print(f"\nFormat Match: {prod_so == bill_so}")
        print(f"Prod SO length: {len(prod_so)}")
        print(f"Bill SO length: {len(bill_so)}")
        
finally:
    db.close()
