from src.db.connection import SessionLocal
from src.db.models import RawZrsd002
import pandas as pd

db = SessionLocal()

try:
    # Get sample raw data
    sample = db.query(RawZrsd002).first()
    
    if sample:
        print("=== RAW ZRSD002 COLUMNS ===")
        # Get all column names from the model
        from sqlalchemy import inspect
        mapper = inspect(RawZrsd002)
        columns = [col.key for col in mapper.attrs]
        
        for col in sorted(columns):
            if col not in ['id', 'created_at']:
                value = getattr(sample, col, None)
                print(f"  {col}: {value}")
                
    # Load to DataFrame to see column names
    print("\n=== CHECKING DIST_CHANNEL ===")
    query = db.query(RawZrsd002).limit(10)
    df = pd.read_sql(query.statement, db.bind)
    
    if 'dist_channel' in df.columns:
        print(f"Column EXISTS in raw data")
        print(f"Sample values: {df['dist_channel'].head().tolist()}")
    else:
        print(f"Column NOT FOUND in raw data")
        print(f"Available columns: {df.columns.tolist()}")
        
finally:
    db.close()
