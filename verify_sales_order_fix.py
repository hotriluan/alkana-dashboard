"""
Verification script for Sales Order metrics fix
Tests that both Executive and Sales dashboards return 3,564 orders for 2025
"""
from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("=" * 60)
print("SALES ORDER METRICS VERIFICATION TEST")
print("=" * 60)

# Test Executive Dashboard
print("\n1. Testing Executive Dashboard (/api/executive/summary)")
response = client.get('/api/executive/summary?start_date=2025-01-01&end_date=2025-12-31')
if response.status_code == 200:
    data = response.json()
    total_orders = data.get('total_orders', 0)
    print(f'   Total Orders: {total_orders}')
    if total_orders == 3564:
        print('   ✓ SUCCESS: Matches ground truth (3,564)')
    else:
        print(f'   ✗ FAIL: Expected 3564, got {total_orders}')
else:
    print(f'   ✗ FAIL: HTTP {response.status_code}')
    print(f'   Error: {response.text}')

# Test Sales Dashboard
print("\n2. Testing Sales Dashboard (/api/sales/summary)")
response = client.get('/api/sales/summary?start_date=2025-01-01&end_date=2025-12-31')
if response.status_code == 200:
    data = response.json()
    total_orders = data.get('total_orders', 0)
    print(f'   Total Orders: {total_orders}')
    if total_orders == 3564:
        print('   ✓ SUCCESS: Matches ground truth (3,564)')
    else:
        print(f'   ✗ FAIL: Expected 3564, got {total_orders}')
else:
    print(f'   ✗ FAIL: HTTP {response.status_code}')
    print(f'   Error: {response.text}')

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
