from src.db.connection import SessionLocal
from src.api.routers.lead_time import trace_batch
import json
import datetime

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def test_trace():
    print("=== TESTING BATCH 25L2460910 ===")
    db = SessionLocal()
    batch_id = "25L2460910"
    
    try:
        result = trace_batch(batch_id, db)
        if result:
            print(json.dumps(result, cls=ComplexEncoder, indent=2))
            print("\n=== ANALYSIS ===")
            print(f"Total Events: {len(result.get('events', []))}")
            for idx, event in enumerate(result.get('events', [])):
                print(f"\nEvent {idx + 1}:")
                print(f"  Stage: {event.get('stage')}")
                print(f"  Date: {event.get('date')}")
                print(f"  Duration: {event.get('duration')} days")
                print(f"  Status: {event.get('status')}")
                print(f"  Details: {event.get('details')}")
        else:
            print("Result is None - Batch not found")
            
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_trace()
