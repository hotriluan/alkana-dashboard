"""
Test netting engine for batch 25L2502310
"""
import pandas as pd
from src.db.connection import SessionLocal
from src.db.models import RawMb51
from src.core.netting import StackNettingEngine

db = SessionLocal()

# Load MB51
mb51_records = db.query(RawMb51).all()
data = []
for r in mb51_records:
    row = {c.name: getattr(r, c.name) for c in r.__table__.columns}
    data.append(row)

mb51_df = pd.DataFrame(data)

# Normalize MVT type
mb51_df['col_1_mvt_type'] = pd.to_numeric(mb51_df['col_1_mvt_type'], errors='coerce').fillna(0).astype(int)

print("Testing netting for batch 25L2502310")
print("=" * 80)

# Check raw data
batch_data = mb51_df[mb51_df['col_6_batch'] == '25L2502310']
mvt_101_1401 = batch_data[(batch_data['col_1_mvt_type'] == 101) & (batch_data['col_2_plant'] == 1401)]

print("\nRaw MB51 data:")
print(f"Total movements for batch: {len(batch_data)}")
print(f"MVT 101 @ Plant 1401: {len(mvt_101_1401)}")

if not mvt_101_1401.empty:
    print("\nMVT 101 records:")
    for _, row in mvt_101_1401.iterrows():
        print(f"  Date: {row['col_0_posting_date']} | MVT: {row['col_1_mvt_type']} | Plant: {row['col_2_plant']}")

# Test netting
engine = StackNettingEngine(mb51_df)
result = engine.apply_stack_netting('25L2502310', 1401, 101, 102)

print(f"\nNetting result:")
print(f"  Is fully reversed: {result.is_fully_reversed}")
print(f"  Total forward (101): {result.total_forward}")
print(f"  Total reverse (102): {result.total_reverse}")
print(f"  Remaining forward: {result.remaining_forward}")
print(f"  Last valid date: {result.last_valid_date}")

if not result.remaining_transactions.empty:
    print(f"\nRemaining transactions:")
    for _, row in result.remaining_transactions.iterrows():
        print(f"  Date: {row['posting_date']} | MVT: {row['mvt_type']}")

db.close()
