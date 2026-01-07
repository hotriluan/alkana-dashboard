"""
Phase 2: Test AR Collection API Endpoint

Test if the backend API returns data correctly.

Skills: backend-development, api-testing
"""
import requests

API_BASE = "http://localhost:8000/api/v1/dashboards"

print("="*80)
print("PHASE 2: AR COLLECTION API TEST")
print("="*80)

# Step 1: Login
print("\n[1] Authentication...")
try:
    response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
        timeout=5
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"  ✅ Authenticated")
    else:
        print(f"  ⚠️ Auth failed: {response.status_code}")
        token = None
except Exception as e:
    print(f"  ⚠️ Auth error: {e}")
    token = None

headers = {"Authorization": f"Bearer {token}"} if token else {}

# Step 2: Test /ar-aging/snapshots
print("\n[2] GET /ar-aging/snapshots")
try:
    response = requests.get(
        f"{API_BASE}/ar-aging/snapshots",
        headers=headers,
        timeout=10
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Snapshots available: {len(data)}")
        for snap in data[:3]:
            print(f"    {snap}")
    else:
        print(f"  Error: {response.text[:200]}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Step 3: Test /ar-aging/summary (without snapshot_date)
print("\n[3] GET /ar-aging/summary (no snapshot_date)")
try:
    response = requests.get(
        f"{API_BASE}/ar-aging/summary",
        headers=headers,
        timeout=30
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Response keys: {list(data.keys())}")
        print(f"  Total target: {data.get('total_target', 0):,.0f}")
        print(f"  Total realization: {data.get('total_realization', 0):,.0f}")
        print(f"  Collection rate: {data.get('collection_rate_pct', 0)}%")
        print(f"  Divisions: {len(data.get('divisions', []))}")
        
        for div in data.get('divisions', []):
            print(f"    {div['division']}: {div['total_target']:,.0f} → {div['total_realization']:,.0f} ({div['collection_rate_pct']}%)")
    else:
        print(f"  Error: {response.text[:500]}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Step 4: Test /ar-aging/customers
print("\n[4] GET /ar-aging/customers")
try:
    response = requests.get(
        f"{API_BASE}/ar-aging/customers",
        headers=headers,
        params={"limit": 5},
        timeout=10
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Customers returned: {len(data)}")
        for cust in data[:3]:
            print(f"    {cust.get('division')}: {cust.get('customer_name')}")
            print(f"      Target: {cust.get('total_target', 0):,.0f}, Realization: {cust.get('total_realization', 0):,.0f}")
    else:
        print(f"  Error: {response.text[:200]}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Summary
print("\n" + "="*80)
print("API TEST SUMMARY")
print("="*80)
print("If all endpoints return 200 with data:")
print("  ✅ Backend is working correctly")
print("  → Issue is in FRONTEND rendering")
print()
print("If endpoints return errors:")
print("  ❌ Backend has issues")
print("  → Need to fix API code")
print("="*80)
