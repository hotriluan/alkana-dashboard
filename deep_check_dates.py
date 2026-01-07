from src.db.connection import SessionLocal
from src.db.models import FactProduction, RawMb51
import pandas as pd

db = SessionLocal()

batch = '25L2502310'

# Check FactProduction
prod = db.query(FactProduction).filter(FactProduction.batch == batch).first()
print(f"FactProduction for {batch}:")
if prod:
    print(f"  Actual finish date: {prod.actual_finish_date}")
    print(f"  Type: {type(prod.actual_finish_date)}")
else:
    print("  NOT FOUND")

# Check RawMb51
mb51_records = db.query(RawMb51).filter(
    RawMb51.col_6_batch == batch,
    RawMb51.col_1_mvt_type == '101',  # Still string in database
    RawMb51.col_2_plant == 1401
).all()

print(f"\nRawMb51 MVT 101 @ Plant 1401:")
if mb51_records:
    for rec in mb51_records:
        print(f"  Posting date: {rec.col_0_posting_date}")
        print(f"  Type: {type(rec.col_0_posting_date)}")
        print(f"  MVT Type: '{rec.col_1_mvt_type}' (type: {type(rec.col_1_mvt_type).__name__})")
else:
    print("  NOT FOUND")

# Calculate expected transit
if prod and mb51_records:
    from datetime import datetime
    
    finish = prod.actual_finish_date
    receipt = mb51_records[0].col_0_posting_date
    
    # Convert to datetime
    if not isinstance(finish, datetime):
        from datetime import datetime as dt
        finish_dt = dt.combine(finish, dt.min.time())
    else:
        finish_dt = finish
    
    if not isinstance(receipt, datetime):
        receipt_dt = dt.combine(receipt, dt.min.time())
    else:
        receipt_dt = receipt
    
    hours = (receipt_dt - finish_dt).total_seconds() / 3600
    
    print(f"\nCalculation:")
    print(f"  Finish: {finish_dt}")
    print(f"  Receipt: {receipt_dt}")
    print(f"  Transit hours: {hours:.1f}")

db.close()
