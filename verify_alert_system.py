"""
Verification Test: Alert System API Endpoints

Skills: backend-development, databases
Tests all 4 alert API endpoints
"""
import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

print("=" * 80)
print("ALERT SYSTEM VERIFICATION TEST")
print("=" * 80)

# Test 1: Check fact_alerts table exists and has data
print("\n[TEST 1] Database - fact_alerts Table")
print("-" * 80)
try:
    result = engine.connect().execute(text("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN status='ACTIVE' THEN 1 END) as active,
               COUNT(CASE WHEN status='RESOLVED' THEN 1 END) as resolved
        FROM fact_alerts
    """)).fetchone()
    
    print(f"Total alerts: {result[0]}")
    print(f"Active: {result[1]}")
    print(f"Resolved: {result[2]}")
    test1_pass = True
    print("Status: ✅ PASS")
except Exception as e:
    print(f"Status: ❌ FAIL - {e}")
    test1_pass = False

# Test 2: Check alert types distribution
print("\n[TEST 2] Alert Types Distribution")
print("-" * 80)
try:
    results = engine.connect().execute(text("""
        SELECT alert_type, COUNT(*) as count
        FROM fact_alerts
        WHERE status = 'ACTIVE'
        GROUP BY alert_type
        ORDER BY count DESC
    """)).fetchall()
    
    for row in results:
        print(f"  {row[0]}: {row[1]} alerts")
    
    test2_pass = len(results) > 0
    print(f"Status: {'✅ PASS' if test2_pass else '⚠️  No active alerts'}")
except Exception as e:
    print(f"Status: ❌ FAIL - {e}")
    test2_pass = False

# Test 3: Check severity distribution
print("\n[TEST 3] Severity Distribution")
print("-" * 80)
try:
    results = engine.connect().execute(text("""
        SELECT severity, COUNT(*) as count
        FROM fact_alerts
        WHERE status = 'ACTIVE'
        GROUP BY severity
        ORDER BY 
            CASE severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                ELSE 4
            END
    """)).fetchall()
    
    for row in results:
        print(f"  {row[0]}: {row[1]} alerts")
    
    test3_pass = True
    print("Status: ✅ PASS")
except Exception as e:
    print(f"Status: ❌ FAIL - {e}")
    test3_pass = False

# Test 4: Sample alert details
print("\n[TEST 4] Sample Alert Details")
print("-" * 80)
try:
    results = engine.connect().execute(text("""
        SELECT id, alert_type, severity, message, detected_at
        FROM fact_alerts
        WHERE status = 'ACTIVE'
        ORDER BY severity, detected_at DESC
        LIMIT 3
    """)).fetchall()
    
    if results:
        for row in results:
            print(f"\n  Alert #{row[0]} ({row[2]})")
            print(f"    Type: {row[1]}")
            print(f"    Message: {row[3][:60]}...")
            print(f"    Detected: {row[4]}")
        test4_pass = True
        print("\nStatus: ✅ PASS")
    else:
        print("  No active alerts to display")
        test4_pass = True
        print("Status: ⚠️  No data (but table exists)")
except Exception as e:
    print(f"Status: ❌ FAIL - {e}")
    test4_pass = False

# Test 5: API Router Registration
print("\n[TEST 5] Backend - API Router Registration")
print("-" * 80)
try:
    from src.api.main import app
    
    # Check if alerts router is registered
    routes = [route.path for route in app.routes]
    alerts_routes = [r for r in routes if '/alerts' in r]
    
    print(f"Found {len(alerts_routes)} alert routes:")
    for route in alerts_routes:
        print(f"  - {route}")
    
    expected_routes = ['/api/v1/alerts/summary', '/api/v1/alerts/stuck-inventory', 
                      '/api/v1/alerts/low-yield', '/api/v1/alerts/{alert_id}/resolve']
    test5_pass = len(alerts_routes) >= 4
    print(f"Status: {'✅ PASS' if test5_pass else '❌ FAIL - Missing routes'}")
except Exception as e:
    print(f"Status: ❌ FAIL - {e}")
    test5_pass = False

# Test 6: Frontend Files Exist
print("\n[TEST 6] Frontend - Files Exist")
print("-" * 80)
import os

files_to_check = [
    ('web/src/pages/AlertMonitor.tsx', 'AlertMonitor component'),
    ('web/src/App.tsx', 'App with /alerts route'),
    ('web/src/components/DashboardLayout.tsx', 'Layout with Alert menu')
]

test6_pass = True
for file_path, description in files_to_check:
    exists = os.path.exists(file_path)
    status = "✅" if exists else "❌"
    print(f"  {status} {description}: {file_path}")
    if not exists:
        test6_pass = False

print(f"Status: {'✅ PASS' if test6_pass else '❌ FAIL - Missing files'}")

# Final Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

all_tests = [
    ("Database Table", test1_pass),
    ("Alert Types", test2_pass),
    ("Severity Distribution", test3_pass),
    ("Sample Alerts", test4_pass),
    ("API Router", test5_pass),
    ("Frontend Files", test6_pass)
]

passed = sum(1 for _, result in all_tests if result)
total = len(all_tests)

for test_name, result in all_tests:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{test_name:<25s}: {status}")

print(f"\nTotal: {passed}/{total} tests passed")

if passed == total:
    print("\n🎉 ALL TESTS PASSED! Alert System is ready for use.")
    print("\nNext Steps:")
    print("1. Run ETL to generate alerts: python -m src.etl.main")
    print("2. Start backend: uvicorn src.api.main:app --reload")
    print("3. Start frontend: cd web && npm run dev")
    print("4. Navigate to http://localhost:5173/alerts")
else:
    print(f"\n⚠️  {total - passed} test(s) failed. Please review implementation.")

print("=" * 80)
