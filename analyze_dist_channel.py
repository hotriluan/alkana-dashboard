from src.db.connection import SessionLocal
from src.db.models import FactBilling

db = SessionLocal()

try:
    # Count dist_channel values
    total = db.query(FactBilling).count()
    
    # NULL values
    null_count = db.query(FactBilling).filter(FactBilling.dist_channel == None).count()
    
    # String 'None' values
    none_str_count = db.query(FactBilling).filter(FactBilling.dist_channel == 'None').count()
    
    # Valid values (not NULL and not 'None')
    valid_count = db.query(FactBilling)\
        .filter(FactBilling.dist_channel.isnot(None))\
        .filter(FactBilling.dist_channel != 'None')\
        .count()
        
    print(f"=== FACTBILLING DIST_CHANNEL ANALYSIS ===")
    print(f"Total Records: {total}")
    print(f"NULL: {null_count}")
    print(f"String 'None': {none_str_count}")
    print(f"Valid Values: {valid_count}")
    
    # Sample valid values
    if valid_count > 0:
        print(f"\n=== SAMPLE VALID CHANNELS ===")
        samples = db.query(FactBilling.so_number, FactBilling.dist_channel)\
            .filter(FactBilling.dist_channel.isnot(None))\
            .filter(FactBilling.dist_channel != 'None')\
            .limit(10).all()
        for so, ch in samples:
            print(f"  SO: '{so}' → Channel: '{ch}'")
    
finally:
    db.close()
