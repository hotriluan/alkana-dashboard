from src.db.connection import SessionLocal
from src.db.models import FactLeadTime
import json

def check_channel_data():
    print("=== CHECKING DISTRIBUTION CHANNEL DATA ===")
    db = SessionLocal()
    
    try:
        # Check if FactLeadTime has channel_code column
        sample = db.query(FactLeadTime).first()
        if sample:
            print(f"\nSample FactLeadTime Record:")
            print(f"  Material: {sample.material_code}")
            print(f"  Order Type: {sample.order_type}")
            
            # Check if channel_code exists
            if hasattr(sample, 'channel_code'):
                print(f"  Channel Code: {sample.channel_code}")
            else:
                print(f"  [ERROR] channel_code column does NOT exist in FactLeadTime")
                
            # Count records with channel
            if hasattr(sample, 'channel_code'):
                total = db.query(FactLeadTime).count()
                with_channel = db.query(FactLeadTime).filter(FactLeadTime.channel_code.isnot(None)).count()
                print(f"\nChannel Data:")
                print(f"  Total Records: {total}")
                print(f"  With Channel: {with_channel}")
                print(f"  Without Channel: {total - with_channel}")
        else:
            print("No records in FactLeadTime")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_channel_data()
