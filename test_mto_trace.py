from src.db.connection import SessionLocal
from src.api.routers.lead_time import trace_batch
import json
import datetime

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def test_mto_trace():
    print("=== TESTING MTO BATCH 25L2474910 ===")
    db = SessionLocal()
    batch_id = "25L2474910"
    
    try:
        result = trace_batch(batch_id, db)
        if result:
            print(json.dumps(result, cls=ComplexEncoder, indent=2))
            print("\n=== STAGE ANALYSIS ===")
            print(f"Total Events: {len(result.get('events', []))}")
            print(f"Order Type: MTO (should show Prep → Prod → Storage → Delivery)")
            print("\nExpected Stages:")
            print("1. Preparation (Violet #8b5cf6)")
            print("2. Production (Blue #3b82f6)")
            print("3. Storage (Amber #f59e0b)")
            print("4. Delivery (Gray #6b7280)")
            print("\nActual Events:")
            for idx, event in enumerate(result.get('events', [])):
                print(f"{idx + 1}. {event.get('stage')} - {event.get('duration')} days")
        else:
            print("Result is None")
            
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_mto_trace()
