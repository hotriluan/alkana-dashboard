import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

tests_passed = []

# Test 1: Data integrity
result = engine.connect().execute(text("SELECT COUNT(*), COUNT(material), COUNT(dist_channel) FROM raw_zrsd006")).fetchone()
test1 = result[1] > 10000 and result[2] > 10000
tests_passed.append(("Data Integrity", test1))
print(f"Test 1 - Data Integrity: {'PASS' if test1 else 'FAIL'}")

# Test 2: JOIN coverage
result = engine.connect().execute(text("""
    SELECT COUNT(*), COUNT(CASE WHEN rz.material IS NOT NULL THEN 1 END)
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()
coverage = result[1]*100/result[0]
test2 = coverage >= 50
tests_passed.append(("JOIN Coverage", test2))
print(f"Test 2 - JOIN Coverage: {'PASS' if test2 else 'FAIL'} ({coverage:.1f}%)")

# Test 3: All channels present
result = engine.connect().execute(text("""
    SELECT DISTINCT rz.dist_channel
    FROM fact_production fp
    JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
        AND rz.dist_channel IN ('11', '12', '13', '15')
""")).fetchall()
channels = [r[0] for r in result]
test3 = all(ch in channels for ch in ['11', '12', '13', '15'])
tests_passed.append(("All Channels", test3))
print(f"Test 3 - All Channels: {'PASS' if test3 else 'FAIL'} ({len(channels)}/4)")

# Test 4: One row per channel
result = engine.connect().execute(text("""
    SELECT COUNT(*)
    FROM (
        SELECT COALESCE(rz.dist_channel, '99')
        FROM fact_production fp
        LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
        WHERE fp.total_leadtime_days IS NOT NULL
        GROUP BY COALESCE(rz.dist_channel, '99')
    ) subq
""")).fetchone()
test4 = result[0] == 5  # 4 channels + No Data
tests_passed.append(("One Row Per Channel", test4))
print(f"Test 4 - One Row Per Channel: {'PASS' if test4 else 'FAIL'} ({result[0]} rows)")

# Test 5: Pydantic model
try:
    from src.api.routers.leadtime import ChannelLeadTime
    fields = ChannelLeadTime.model_fields
    test5 = all(f in fields for f in ['mto_orders', 'mts_orders', 'total_orders'])
    tests_passed.append(("Pydantic Model", test5))
    print(f"Test 5 - Pydantic Model: {'PASS' if test5 else 'FAIL'}")
except:
    tests_passed.append(("Pydantic Model", False))
    print(f"Test 5 - Pydantic Model: FAIL")

# Summary
passed = sum(1 for _, p in tests_passed if p)
total = len(tests_passed)
print(f"\nSummary: {passed}/{total} tests passed")

if passed == total:
    print("SUCCESS: All tests passed!")
else:
    print("WARNING: Some tests failed")
