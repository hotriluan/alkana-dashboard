from src.db.connection import SessionLocal
from src.db.models import RawZrsd002
import json

db = SessionLocal()

try:
    sample = db.query(RawZrsd002).first()
    
    if sample and sample.raw_data:
        print("=== RAW_DATA JSON KEYS ===")
        data = json.loads(sample.raw_data) if isinstance(sample.raw_data, str) else sample.raw_data
        
        for key in sorted(data.keys()):
            print(f"  '{key}': {data[key]}")
            
        # Look for channel-related keys
        print("\n=== CHANNEL-RELATED KEYS ===")
        for key in data.keys():
            if 'channel' in key.lower() or 'dist' in key.lower():
                print(f"  FOUND: '{key}' = {data[key]}")
                
finally:
    db.close()
