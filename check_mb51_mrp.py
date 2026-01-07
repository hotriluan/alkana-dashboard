from src.db.connection import SessionLocal
from src.db.models import RawMb51
import pandas as pd

db = SessionLocal()

try:
    # Get sample mb51
    sample = db.query(RawMb51).first()
    
    if sample:
        print("=== MB51 COLUMNS ===")
        from sqlalchemy import inspect
        mapper = inspect(RawMb51)
        columns = [col.key for col in mapper.attrs if col.key not in ['id', 'created_at', 'raw_data']]
        
        for col in sorted(columns):
            value = getattr(sample, col, None)
            print(f"  {col}: {value}")
            
        # Check if mrp_controller exists
        if hasattr(sample, 'col_10_mrp_controller'):
            print(f"\n✓ MRP Controller column EXISTS: {sample.col_10_mrp_controller}")
        else:
            print("\n✗ MRP Controller column NOT FOUND")
            
finally:
    db.close()
