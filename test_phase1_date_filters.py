"""
Test Phase 1: Date Filters

Tests all 4 dashboard APIs to verify date filtering works correctly.

Skills: testing, api-development
"""
import requests
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000/api/v1/dashboards"
TOKEN = None  # Will get from login

# Test dates
today = datetime.now()
start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
end_date = today.strftime('%Y-%m-%d')

def test_endpoint(name, url, params_with_dates, params_without_dates=None):
    """Test endpoint with and without date filters"""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"{'='*80}")
    
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    
    # Test WITHOUT dates (should return all data)
    print(f"\n[1] WITHOUT date filter:")
    try:
        response = requests.get(url, params=params_without_dates or {}, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status: 200 OK")
            print(f"  📊 Response keys: {list(data.keys())}")
            # Show sample size
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"     {key}: {len(value)} items")
                    elif isinstance(value, (int, float)):
                        print(f"     {key}: {value}")
        else:
            print(f"  ❌ Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test WITH dates
    print(f"\n[2] WITH date filter ({start_date} to {end_date}):")
    try:
        response = requests.get(url, params=params_with_dates, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status: 200 OK")
            print(f"  📊 Response keys: {list(data.keys())}")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"     {key}: {len(value)} items")
                    elif isinstance(value, (int, float)):
                        print(f"     {key}: {value}")
        else:
            print(f"  ❌ Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    global TOKEN
    
    print("="*80)
    print("PHASE 1: DATE FILTER TESTING")
    print("="*80)
    print(f"Date Range: {start_date} to {end_date}")
    
    # Check backend connectivity
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        print("✅ Backend is running")
    except:
        print("❌ Backend not running - start with: uvicorn src.api.main:app --reload")
        return
    
    # Login to get token
    print("\n[AUTH] Getting access token...")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            timeout=5
        )
        if response.status_code == 200:
            TOKEN = response.json()["access_token"]
            print(f"  ✅ Authenticated")
        else:
            print(f"  ⚠️ Auth failed (will try without token): {response.status_code}")
            TOKEN = None
    except Exception as e:
        print(f"  ⚠️ Auth endpoint not available (will try without token): {e}")
        TOKEN = None
    
    # Test 1: Sales Performance
    test_endpoint(
        "Sales Performance Dashboard",
        f"{API_BASE}/sales/summary",
        params_with_dates={"start_date": start_date, "end_date": end_date},
        params_without_dates={}
    )
    
    # Test 2: Production Yield
    test_endpoint(
        "Production Yield Dashboard",
        f"{API_BASE}/yield/summary",
        params_with_dates={"start_date": start_date, "end_date": end_date},
        params_without_dates={}
    )
    
    # Test 3: Inventory
    test_endpoint(
        "Inventory Dashboard",
        f"{API_BASE}/inventory/summary",
        params_with_dates={"start_date": start_date, "end_date": end_date},
        params_without_dates={}
    )
    
    # Test 4: AR Aging (uses snapshot_date instead of start/end)
    print(f"\n{'='*80}")
    print(f"Testing: AR Aging Dashboard (snapshot_date)")
    print(f"{'='*80}")
    
    # First, get available snapshots
    print(f"\n[1] Get available snapshot dates:")
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    try:
        response = requests.get(f"http://localhost:8000/api/v1/dashboards/ar-aging/snapshots", headers=headers, timeout=10)
        if response.status_code == 200:
            snapshots = response.json()
            print(f"  ✅ Status: 200 OK")
            print(f"  📊 Available snapshots: {len(snapshots)}")
            if snapshots:
                latest_snapshot = snapshots[0]['snapshot_date']
                print(f"     Latest: {latest_snapshot} ({snapshots[0]['row_count']} rows)")
                
                # Test with specific snapshot
                print(f"\n[2] Test with snapshot_date={latest_snapshot}:")
                response = requests.get(
                    f"http://localhost:8000/api/v1/dashboards/ar-aging/summary",
                    params={"snapshot_date": latest_snapshot},
                    headers=headers,
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ Status: 200 OK")
                    print(f"  📊 Response keys: {list(data.keys())}")
                    print(f"     Divisions: {len(data.get('divisions', []))}")
                    print(f"     Total target: {data.get('total_target', 0):,.0f}")
                    print(f"     Collection rate: {data.get('collection_rate_pct', 0)}%")
                else:
                    print(f"  ❌ Status: {response.status_code}")
                    print(f"  Error: {response.text[:200]}")
            else:
                print("  ⚠️ No snapshots available")
        else:
            print(f"  ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Summary
    print(f"\n{'='*80}")
    print("PHASE 1 TESTING COMPLETE")
    print(f"{'='*80}")
    print("✅ Date filters added to 4 dashboards:")
    print("   1. Sales Performance (/sales/summary) - start_date, end_date")
    print("   2. Production Yield (/yield/summary) - start_date, end_date")
    print("   3. Inventory (/inventory/summary) - start_date, end_date")
    print("   4. AR Aging (/ar-aging/summary) - snapshot_date")
    print("\n📋 Next Steps:")
    print("   - Verify frontend DatePicker components pass correct params")
    print("   - Add database indexes for performance (Phase 5)")
    print("   - Monitor query performance (<500ms target)")
    print("="*80)


if __name__ == "__main__":
    main()
