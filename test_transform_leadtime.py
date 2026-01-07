import sys
import traceback
from src.etl.transform import Transformer
from src.db.connection import SessionLocal

try:
    print("=== TESTING TRANSFORM_LEAD_TIME ===")
    db = SessionLocal()
    transformer = Transformer(db)
    transformer.transform_lead_time()
    print("\nSUCCESS!")
except Exception as e:
    print(f"\nERROR: {e}")
    print("\nFull Traceback:")
    traceback.print_exc()
finally:
    if 'db' in locals():
        db.close()
