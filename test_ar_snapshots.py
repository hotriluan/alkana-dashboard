"""
Test AR Snapshot Features

Skills: api-testing, ui-ux-validation
"""
import sys
sys.path.insert(0, '.')

from src.db.connection import SessionLocal
from src.db.models import RawZrfi005, FactArAging
from src.etl.transform import Transformer
from sqlalchemy import func

db = SessionLocal()

print("=" * 70)
print("TEST: AR Snapshot Features")
print("=" * 70)

# Test 1: List available snapshots
print("\n1. Available Snapshots:")
snapshots = db.query(
    RawZrfi005.snapshot_date,
    func.count(RawZrfi005.id).label('count')
).filter(
    RawZrfi005.snapshot_date != None
).group_by(
    RawZrfi005.snapshot_date
).order_by(
    RawZrfi005.snapshot_date.desc()
).all()

for snap, count in snapshots:
    print(f"  📅 {snap.strftime('%Y-%m-%d')}: {count} rows")

# Test 2: Transform with specific date
if len(snapshots) >= 2:
    test_date = snapshots[1][0].strftime('%Y-%m-%d')  # Second latest
    print(f"\n2. Test transform with date: {test_date}")
    
    transformer = Transformer(db)
    transformer.transform_zrfi005(target_date=test_date)
    
    # Check results
    total = db.query(func.count(FactArAging.id)).scalar()
    total_target = db.query(func.sum(FactArAging.total_target)).scalar()
    
    print(f"  Result: {total} rows in fact_ar_aging")
    print(f"  Total Target: {total_target:,.0f} VND")

# Test 3: Transform with latest (None parameter)
print(f"\n3. Test transform with latest snapshot:")
transformer = Transformer(db)
transformer.transform_zrfi005()

total = db.query(func.count(FactArAging.id)).scalar()
total_target = db.query(func.sum(FactArAging.total_target)).scalar()

print(f"  Result: {total} rows in fact_ar_aging")
print(f"  Total Target: {total_target:,.0f} VND")

db.close()

print("\n" + "=" * 70)
print("✅ All tests completed!")
print("=" * 70)
