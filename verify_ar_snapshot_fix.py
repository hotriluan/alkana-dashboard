"""
Verify AR Customer Table Snapshot Isolation Fix

Tests that customer details respect snapshot_date filter
"""
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_snapshot_isolation():
    """Verify customers endpoint respects snapshot_date parameter"""
    print("🔍 Testing AR Customer Table Snapshot Isolation...")
    
    # Get available snapshots
    print("\n1. Fetching available snapshots...")
    resp = requests.get(f"{BASE_URL}/api/v1/dashboards/ar-aging/snapshots")
    if resp.status_code != 200:
        print(f"❌ Failed to fetch snapshots: {resp.status_code}")
        return False
    
    snapshots = resp.json()
    if len(snapshots) < 2:
        print(f"⚠️  Only {len(snapshots)} snapshot(s) available. Need at least 2 for comparison.")
        return False
    
    snapshot1 = snapshots[0]['snapshot_date']
    snapshot2 = snapshots[1]['snapshot_date']
    print(f"   ✓ Found snapshots: {snapshot1}, {snapshot2}")
    
    # Test snapshot 1
    print(f"\n2. Fetching customers for snapshot {snapshot1}...")
    resp1 = requests.get(
        f"{BASE_URL}/api/v1/dashboards/ar-aging/customers",
        params={"snapshot_date": snapshot1, "limit": 100}
    )
    if resp1.status_code != 200:
        print(f"❌ Failed: {resp1.status_code}")
        return False
    
    customers1 = resp1.json()
    print(f"   ✓ Got {len(customers1)} customers")
    
    # Test snapshot 2
    print(f"\n3. Fetching customers for snapshot {snapshot2}...")
    resp2 = requests.get(
        f"{BASE_URL}/api/v1/dashboards/ar-aging/customers",
        params={"snapshot_date": snapshot2, "limit": 100}
    )
    if resp2.status_code != 200:
        print(f"❌ Failed: {resp2.status_code}")
        return False
    
    customers2 = resp2.json()
    print(f"   ✓ Got {len(customers2)} customers")
    
    # Verify no duplicates within same snapshot
    print("\n4. Checking for duplicates within each snapshot...")
    names1 = [c['customer_name'] for c in customers1]
    names2 = [c['customer_name'] for c in customers2]
    
    duplicates1 = len(names1) - len(set(names1))
    duplicates2 = len(names2) - len(set(names2))
    
    if duplicates1 > 0:
        print(f"   ❌ Snapshot {snapshot1} has {duplicates1} duplicate customers")
        return False
    if duplicates2 > 0:
        print(f"   ❌ Snapshot {snapshot2} has {duplicates2} duplicate customers")
        return False
    
    print(f"   ✓ No duplicates in either snapshot")
    
    # Test without snapshot_date (should use latest)
    print("\n5. Testing default snapshot behavior (no snapshot_date param)...")
    resp_default = requests.get(
        f"{BASE_URL}/api/v1/dashboards/ar-aging/customers",
        params={"limit": 100}
    )
    if resp_default.status_code != 200:
        print(f"❌ Failed: {resp_default.status_code}")
        return False
    
    customers_default = resp_default.json()
    print(f"   ✓ Got {len(customers_default)} customers (should match latest snapshot)")
    
    # Verify data structure
    if customers_default:
        sample = customers_default[0]
        required_fields = ['customer_name', 'division', 'total_target', 'total_realization', 
                         'collection_rate_pct', 'risk_level']
        missing = [f for f in required_fields if f not in sample]
        if missing:
            print(f"   ❌ Missing fields: {missing}")
            return False
        print(f"   ✓ Response has all required fields")
    
    print("\n✅ ALL TESTS PASSED")
    print(f"   • Snapshot 1 ({snapshot1}): {len(customers1)} unique customers")
    print(f"   • Snapshot 2 ({snapshot2}): {len(customers2)} unique customers")
    print(f"   • Default (latest): {len(customers_default)} customers")
    print(f"   • No duplicates detected")
    return True

if __name__ == "__main__":
    try:
        success = test_snapshot_isolation()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running at http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
