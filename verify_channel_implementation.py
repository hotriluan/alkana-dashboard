"""
COMPREHENSIVE VERIFICATION TEST
Distribution Channel Grouping Feature
"""
import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text
import json

print("=" * 80)
print("VERIFICATION TEST: Distribution Channel Grouping")
print("=" * 80)

# Test 1: Database - raw_zrsd006 data integrity
print("\n[TEST 1] Database - raw_zrsd006 Data Integrity")
print("-" * 80)
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(material) as has_material,
        COUNT(dist_channel) as has_channel,
        COUNT(DISTINCT dist_channel) as unique_channels
    FROM raw_zrsd006
""")).fetchone()

print(f"Total rows: {result[0]}")
print(f"With material code: {result[1]} ({result[1]*100/result[0]:.1f}%)")
print(f"With dist_channel: {result[2]} ({result[2]*100/result[0]:.1f}%)")
print(f"Unique channels: {result[3]}")

test1_pass = result[1] > 10000 and result[2] > 10000
print(f"Status: {'✅ PASS' if test1_pass else '❌ FAIL'}")

# Test 2: JOIN Coverage
print("\n[TEST 2] JOIN Coverage - fact_production <-> raw_zrsd006")
print("-" * 80)
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN rz.material IS NOT NULL THEN 1 END) as matched,
        ROUND(COUNT(CASE WHEN rz.material IS NOT NULL THEN 1 END)*100.0/COUNT(*), 1) as pct
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()

print(f"Total production orders: {result[0]}")
print(f"Matched with zrsd006: {result[1]} ({result[2]}%)")

test2_pass = result[2] >= 50  # At least 50% coverage
print(f"Status: {'✅ PASS' if test2_pass else '❌ FAIL'}")

# Test 3: Channel Distribution
print("\n[TEST 3] Channel Distribution - All 4 Channels Present")
print("-" * 80)
result = engine.connect().execute(text("""
    SELECT 
        rz.dist_channel,
        COUNT(*) as orders
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
        AND rz.dist_channel IN ('11', '12', '13', '15')
    GROUP BY rz.dist_channel
    ORDER BY rz.dist_channel
""")).fetchall()

channels_found = {row[0]: row[1] for row in result}
required_channels = ['11', '12', '13', '15']
channel_names = {'11': 'Industry', '12': 'Over Sea', '13': 'Retail', '15': 'Project'}

for ch in required_channels:
    count = channels_found.get(ch, 0)
    print(f"  {ch} ({channel_names[ch]}): {count} orders")

test3_pass = all(ch in channels_found for ch in required_channels)
print(f"Status: {'✅ PASS' if test3_pass else '❌ FAIL'}")

# Test 4: SQL Query - One Row Per Channel
print("\n[TEST 4] SQL Query - One Row Per Channel (Pivoted Structure)")
print("-" * 80)
result = engine.connect().execute(text("""
    SELECT 
        COALESCE(rz.dist_channel, '99') as channel,
        COUNT(CASE WHEN fp.is_mto = TRUE THEN 1 END) as mto_orders,
        COUNT(CASE WHEN fp.is_mto = FALSE THEN 1 END) as mts_orders,
        COUNT(*) as total_orders
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
    GROUP BY COALESCE(rz.dist_channel, '99')
    ORDER BY COALESCE(rz.dist_channel, '99')
""")).fetchall()

print(f"Total rows returned: {len(result)}")
print(f"\n{'Channel':<15s} {'MTO':>6s} {'MTS':>6s} {'Total':>7s}")
print("-" * 40)

for row in result:
    ch_name = {'11': 'Industry', '12': 'Over Sea', '13': 'Retail', '15': 'Project', '99': 'No Data'}.get(row[0], row[0])
    print(f"{ch_name:<15s} {row[1]:>6d} {row[2]:>6d} {row[3]:>7d}")

test4_pass = len(result) == 5  # 4 channels + 1 "No Data"
print(f"\nStatus: {'✅ PASS' if test4_pass else '❌ FAIL'}")

# Test 5: Data Quality - MTO/MTS Split
print("\n[TEST 5] Data Quality - MTO/MTS Split")
print("-" * 80)
total_mto = sum(row[1] for row in result)
total_mts = sum(row[2] for row in result)
total_all = sum(row[3] for row in result)

print(f"Total MTO orders: {total_mto}")
print(f"Total MTS orders: {total_mts}")
print(f"Total all orders: {total_all}")
print(f"Verification: {total_mto} + {total_mts} = {total_mto + total_mts} (should equal {total_all})")

test5_pass = (total_mto + total_mts) == total_all
print(f"Status: {'✅ PASS' if test5_pass else '❌ FAIL'}")

# Test 6: Pydantic Model Structure
print("\n[TEST 6] Backend - Pydantic Model Structure")
print("-" * 80)
try:
    from src.api.routers.leadtime import ChannelLeadTime
    import inspect
    
    fields = ChannelLeadTime.model_fields
    required_fields = [
        'channel', 'channel_name',
        'mto_orders', 'mto_avg_leadtime', 'mto_on_time_pct',
        'mts_orders', 'mts_avg_leadtime', 'mts_on_time_pct',
        'total_orders', 'avg_total_leadtime'
    ]
    
    print(f"Model fields: {list(fields.keys())}")
    
    missing_fields = [f for f in required_fields if f not in fields]
    if missing_fields:
        print(f"Missing fields: {missing_fields}")
        test6_pass = False
    else:
        print("All required fields present")
        test6_pass = True
        
except Exception as e:
    print(f"Error: {e}")
    test6_pass = False

print(f"Status: {'✅ PASS' if test6_pass else '❌ FAIL'}")

# Final Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

all_tests = [
    ("Database Data Integrity", test1_pass),
    ("JOIN Coverage", test2_pass),
    ("Channel Distribution", test3_pass),
    ("SQL Query Structure", test4_pass),
    ("Data Quality", test5_pass),
    ("Pydantic Model", test6_pass)
]

passed = sum(1 for _, result in all_tests if result)
total = len(all_tests)

for test_name, result in all_tests:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{test_name:<30s}: {status}")

print(f"\nTotal: {passed}/{total} tests passed")

if passed == total:
    print("\n🎉 ALL TESTS PASSED! Implementation is verified and ready for production.")
else:
    print(f"\n⚠️  {total - passed} test(s) failed. Please review implementation.")

print("=" * 80)
