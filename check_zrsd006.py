from src.db.connection import SessionLocal
from src.db.models import RawZrsd006
import json

db = SessionLocal()

try:
    sample = db.query(RawZrsd006).first()
    
    if sample and sample.raw_data:
        print("=== ZRSD006 RAW_DATA KEYS ===")
        data = json.loads(sample.raw_data) if isinstance(sample.raw_data, str) else sample.raw_data
        
        for key in sorted(data.keys()):
            print(f"  '{key}': {data[key]}")
            
        # Look for channel and material
        print("\n=== KEY FIELDS ===")
        for key in ['Material', 'Dist Channel', 'Distribution Channel', 'Channel']:
            if key in data:
                print(f"  {key}: {data[key]}")
                
finally:
    db.close()
