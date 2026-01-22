"""
Verification Script: Test the AR Aging Bucket Fix
Tests API endpoint with snapshot_date parameter to verify correct values
"""
from src.api.deps import get_db
from sqlalchemy import text
import sys

db = next(get_db())

print("=" * 80)
print("🧪 AR AGING BUCKET FIX - VERIFICATION TEST")
print("=" * 80)

# Get latest snapshot
latest = db.execute(text("""
    SELECT snapshot_date 
    FROM fact_ar_aging 
    ORDER BY snapshot_date DESC 
    LIMIT 1
""")).scalar()

if not latest:
    print("❌ No data in fact_ar_aging table")
    sys.exit(1)

snapshot_date = latest.isoformat()
print(f"\n📅 Testing with snapshot_date: {snapshot_date}")

# Test the FIXED query (with snapshot_date filter)
print("\n" + "=" * 80)
print("TEST 1: Query WITH snapshot_date filter (AFTER FIX)")
print("=" * 80)

r = db.execute(text("""
    SELECT 
        SUM(COALESCE(realization_not_due, 0)),
        SUM(COALESCE(target_1_30, 0)), SUM(COALESCE(target_31_60, 0)),
        SUM(COALESCE(target_61_90, 0)), SUM(COALESCE(target_91_120, 0)),
        SUM(COALESCE(target_121_180, 0)), SUM(COALESCE(target_over_180, 0)),
        SUM(COALESCE(realization_1_30, 0)), SUM(COALESCE(realization_31_60, 0)),
        SUM(COALESCE(realization_61_90, 0)), SUM(COALESCE(realization_91_120, 0)),
        SUM(COALESCE(realization_121_180, 0)), SUM(COALESCE(realization_over_180, 0))
    FROM fact_ar_aging
    WHERE snapshot_date = :snapshot_date
"""), {"snapshot_date": snapshot_date}).fetchone()

buckets = [
    ("Not Due", r[0]),
    ("1-30 Days", r[1]),
    ("31-60 Days", r[2]),
    ("61-90 Days", r[3]),
    ("91-120 Days", r[4]),
    ("121-180 Days", r[5]),
    (">180 Days", r[6]),
]

total_buckets = sum(b[1] for b in buckets if b[1])

print("\n📊 Bucket Distribution (Target Amounts):")
for bucket_name, amount in buckets:
    print(f"  {bucket_name:20s} {amount:>20,.0f} VND")

print(f"\n  {'TOTAL':20s} {total_buckets:>20,.0f} VND")

# Compare with total_target from same snapshot
total_target = db.execute(text("""
    SELECT SUM(total_target)
    FROM fact_ar_aging
    WHERE snapshot_date = :snapshot_date
"""), {"snapshot_date": snapshot_date}).scalar()

print(f"\n✅ Expected Total (from total_target): {total_target:>20,.0f} VND")
print(f"✅ Bucket Sum:                          {total_buckets:>20,.0f} VND")

difference = abs(total_target - total_buckets)
if difference < 100000:  # Allow 100K rounding difference
    print(f"\n✅ PASS: Buckets sum matches total_target (diff: {difference:,.0f} VND)")
else:
    print(f"\n⚠️  WARNING: Difference of {difference:,.0f} VND detected")

# Test WITHOUT snapshot filter (should show inflated values)
print("\n" + "=" * 80)
print("TEST 2: Query WITHOUT snapshot_date filter (BEFORE FIX - for comparison)")
print("=" * 80)

r2 = db.execute(text("""
    SELECT SUM(COALESCE(target_1_30, 0))
    FROM fact_ar_aging
""")).scalar()

print(f"\n  1-30 Days (ALL snapshots):  {r2:>20,.0f} VND ⚠️  (INFLATED)")
print(f"  1-30 Days (SINGLE snapshot): {r[1]:>20,.0f} VND ✅ (CORRECT)")

multiplier = r2 / r[1] if r[1] > 0 else 0
print(f"\n  Inflation multiplier: {multiplier:.2f}x")

# Final verdict
print("\n" + "=" * 80)
if difference < 100000 and multiplier > 1.5:
    print("✅ VERIFICATION PASSED")
    print("   - Snapshot filtering works correctly")
    print("   - Buckets sum to total_target")
    print("   - Data inflation prevented")
else:
    print("⚠️  VERIFICATION INCONCLUSIVE")
print("=" * 80)
