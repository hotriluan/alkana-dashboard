"""Debug transit time - detailed check"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.db.connection import engine, SessionLocal
from src.db.models import FactProduction
from sqlalchemy import text

# Load movements
movements_df = pd.read_sql(
    text("SELECT batch, posting_date FROM fact_inventory WHERE mvt_type = 101 AND batch IS NOT NULL LIMIT 1000"),
    engine.connect()
)

print(f"Loaded {len(movements_df)} movements")
print(f"Sample posting_date type: {type(movements_df['posting_date'].iloc[0])}")
print(f"Sample posting_date value: {movements_df['posting_date'].iloc[0]}")

# Get production orders
db = SessionLocal()
orders = db.query(FactProduction).filter(FactProduction.actual_finish_date.isnot(None)).limit(10).all()

print(f"\nTesting {len(orders)} orders:")
for order in orders:
    batch = order.batch
    finish_date = order.actual_finish_date
    
    mvt_101 = movements_df[movements_df['batch'] == batch]
    
    if not mvt_101.empty:
        receipt_date = mvt_101['posting_date'].min()
        
        print(f"\nBatch: {batch}")
        print(f"  Finish: {finish_date} (type: {type(finish_date)})")
        print(f"  Receipt: {receipt_date} (type: {type(receipt_date)})")
        
        # Test conversion
        if isinstance(receipt_date, pd.Timestamp):
            receipt_clean = receipt_date.date()
            print(f"  Receipt (converted): {receipt_clean} (type: {type(receipt_clean)})")
        else:
            receipt_clean = receipt_date
            print(f"  Receipt (no conversion needed)")
        
        # Calculate
        try:
            transit = (receipt_clean - finish_date).days
            print(f"  Transit time: {transit} days")
        except Exception as e:
            print(f"  Error: {e}")

db.close()
