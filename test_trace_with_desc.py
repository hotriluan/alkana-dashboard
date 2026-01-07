from src.db.connection import SessionLocal
from src.api.routers.lead_time import trace_batch
import json

db = SessionLocal()

try:
    # Test with batch 25L2460910
    result = trace_batch("25L2460910", db)
    
    print("=== TRACE API RESPONSE ===")
    print(json.dumps(result, indent=2, default=str))
    
    if result:
        print(f"\n=== PRODUCT INFO ===")
        print(f"Product Code: {result.get('product')}")
        print(f"Product Description: {result.get('product_description')}")
        
finally:
    db.close()
