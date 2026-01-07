from src.db.connection import SessionLocal
from src.db.models import FactProduction, FactBilling

db = SessionLocal()

try:
    # Check SO 210033967 in both tables
    test_so = "210033967"
    
    print(f"=== CHECKING SO: {test_so} ===\n")
    
    # Check in FactProduction
    prod = db.query(FactProduction).filter(FactProduction.sales_order == test_so).first()
    if prod:
        print(f"FactProduction:")
        print(f"  Sales Order: '{prod.sales_order}' (type: {type(prod.sales_order)})")
        print(f"  Order Number: {prod.order_number}")
        print(f"  Is MTO: {prod.is_mto}")
    else:
        print(f"NOT FOUND in FactProduction")
        
    # Check in FactBilling
    bill = db.query(FactBilling).filter(FactBilling.so_number == test_so).first()
    if bill:
        print(f"\nFactBilling:")
        print(f"  SO Number: '{bill.so_number}' (type: {type(bill.so_number)})")
        print(f"  Dist Channel: '{bill.dist_channel}'")
    else:
        print(f"\nNOT FOUND in FactBilling")
        
    # Check all SOs in FactBilling
    print(f"\n=== SAMPLE SOs FROM FACTBILLING ===")
    samples = db.query(FactBilling.so_number, FactBilling.dist_channel)\
        .filter(FactBilling.so_number.isnot(None))\
        .filter(FactBilling.dist_channel.isnot(None))\
        .limit(10).all()
    for so, ch in samples:
        print(f"  SO: '{so}' → Channel: '{ch}'")
        
finally:
    db.close()
