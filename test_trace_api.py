from src.db.connection import SessionLocal
from src.api.routers.lead_time import trace_batch
import json

def test_trace():
    print("=== TESTING BATCH TRACE API LOGIC ===")
    db = SessionLocal()
    batch_id = "25L2473710"
    
    try:
        result = trace_batch(batch_id, db)
        if result:
            print(json.dumps(result, cls=ComplexEncoder, indent=2))
        else:
            print("Result is None")
            
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        db.close()

import datetime
from json import JSONEncoder

class ComplexEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

if __name__ == "__main__":
    test_trace()
