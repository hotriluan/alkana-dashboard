from src.db.connection import SessionLocal
from src.db.models import RawZrsd006
import json

db = SessionLocal()

try:
    sample = db.query(RawZrsd006).first()
    
    if sample:
        print("=== ZRSD006 RECORD ===")
        print(f"ID: {sample.id}")
        print(f"Material (column): {sample.material}")
        print(f"Dist Channel (column): {sample.dist_channel}")
        
        if sample.raw_data:
            data = json.loads(sample.raw_data) if isinstance(sample.raw_data, str) else sample.raw_data
            print(f"\n=== RAW_DATA ===")
            print(f"Material Code: {data.get('Material Code')}")
            print(f"Distribution Channel: {data.get('Distribution Channel')}")
            
finally:
    db.close()
