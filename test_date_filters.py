"""
Test Date Filter Implementation

Skills: backend-development, testing, debugging
Tests all updated APIs to verify date filtering works correctly
"""
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_executive_apis():
    """Test Executive Dashboard APIs with date filters"""
    print("\n" + "="*60)
    print("TESTING EXECUTIVE DASHBOARD APIS")
    print("="*60)
    
    # Test without date filter (baseline)
    print("\n1. Testing /api/v1/dashboards/executive/summary WITHOUT date filter:")
    response = requests.get(f"{BASE_URL}/api/v1/dashboards/executive/summary")
    if response.status_code == 200:
        baseline = response.json()
        print(f"   ✓ Total Revenue: {baseline.get('total_revenue', 0):,.0f}")
        print(f"   ✓ Total Orders: {baseline.get('total_orders', 0)}")
        print(f"   ✓ Total Customers: {baseline.get('total_customers', 0)}")
    else:
        print(f"   ✗ Error: {response.status_code}")
        return
    
    # Test with 30-day date filter
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    print(f"\n2. Testing /api/v1/dashboards/executive/summary WITH date filter ({start_date.date()} to {end_date.date()}):")
    response = requests.get(
        f"{BASE_URL}/api/v1/dashboards/executive/summary",
        params={
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
    )
    if response.status_code == 200:
        filtered = response.json()
        print(f"   ✓ Total Revenue: {filtered.get('total_revenue', 0):,.0f}")
        print(f"   ✓ Total Orders: {filtered.get('total_orders', 0)}")
        print(f"   ✓ Total Customers: {filtered.get('total_customers', 0)}")
        
        # Check if values are different (filter should work)
        if filtered != baseline:
            print(f"   ✓ PASS: Date filter is working! Values changed.")
        else:
            print(f"   ⚠ WARNING: Values are the same. All data might be within 30 days.")
    else:
        print(f"   ✗ Error: {response.status_code} - {response.text}")
    
    # Test revenue by division
    print(f"\n3. Testing /api/v1/dashboards/executive/revenue-by-division WITH date filter:")
    response = requests.get(
        f"{BASE_URL}/api/v1/dashboards/executive/revenue-by-division",
        params={
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "limit": 5
        }
    )
    if response.status_code == 200:
        divisions = response.json()
        print(f"   ✓ Retrieved {len(divisions)} divisions")
        if divisions:
            print(f"   ✓ Top division: {divisions[0].get('division_code')} - {divisions[0].get('revenue', 0):,.0f}")
    else:
        print(f"   ✗ Error: {response.status_code}")


def test_leadtime_apis():
    """Test Lead Time Dashboard APIs with date filters"""
    print("\n" + "="*60)
    print("TESTING LEAD TIME DASHBOARD APIS")
    print("="*60)
    
    # Test without filter
    print("\n1. Testing /api/v1/leadtime/summary WITHOUT date filter:")
    response = requests.get(f"{BASE_URL}/api/v1/leadtime/summary")
    if response.status_code == 200:
        baseline = response.json()
        print(f"   ✓ Total Orders: {baseline.get('total_orders', 0)}")
        print(f"   ✓ Avg MTO Lead Time: {baseline.get('avg_mto_leadtime', 0):.1f} days")
        print(f"   ✓ On Time %: {baseline.get('on_time_pct', 0):.1f}%")
    else:
        print(f"   ✗ Error: {response.status_code}")
        return
    
    # Test with 30-day filter
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    print(f"\n2. Testing /api/v1/leadtime/summary WITH date filter ({start_date.date()} to {end_date.date()}):")
    response = requests.get(
        f"{BASE_URL}/api/v1/leadtime/summary",
        params={
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
    )
    if response.status_code == 200:
        filtered = response.json()
        print(f"   ✓ Total Orders: {filtered.get('total_orders', 0)}")
        print(f"   ✓ Avg MTO Lead Time: {filtered.get('avg_mto_leadtime', 0):.1f} days")
        print(f"   ✓ On Time %: {filtered.get('on_time_pct', 0):.1f}%")
        
        if filtered != baseline:
            print(f"   ✓ PASS: Date filter is working! Values changed.")
        else:
            print(f"   ⚠ WARNING: Values are the same.")
    else:
        print(f"   ✗ Error: {response.status_code} - {response.text}")
    
    # Test breakdown
    print(f"\n3. Testing /api/v1/leadtime/breakdown WITH date filter:")
    response = requests.get(
        f"{BASE_URL}/api/v1/leadtime/breakdown",
        params={
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
    )
    if response.status_code == 200:
        breakdown = response.json()
        print(f"   ✓ Retrieved {len(breakdown)} categories")
        for cat in breakdown:
            print(f"   ✓ {cat['order_category']}: {cat['order_count']} orders, {cat['avg_total']:.1f} days avg")
    else:
        print(f"   ✗ Error: {response.status_code}")


def test_alert_apis():
    """Test Alert Monitor APIs with date filters"""
    print("\n" + "="*60)
    print("TESTING ALERT MONITOR APIS")
    print("="*60)
    
    # Test without filter
    print("\n1. Testing /api/v1/alerts/summary WITHOUT date filter:")
    response = requests.get(f"{BASE_URL}/api/v1/alerts/summary")
    if response.status_code == 200:
        baseline = response.json()
        print(f"   ✓ Total Alerts: {baseline.get('total', 0)}")
        print(f"   ✓ Critical: {baseline.get('critical', 0)}")
        print(f"   ✓ High: {baseline.get('high', 0)}")
    else:
        print(f"   ✗ Error: {response.status_code}")
        return
    
    # Test with 7-day filter
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    print(f"\n2. Testing /api/v1/alerts/summary WITH date filter ({start_date.date()} to {end_date.date()}):")
    response = requests.get(
        f"{BASE_URL}/api/v1/alerts/summary",
        params={
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
    )
    if response.status_code == 200:
        filtered = response.json()
        print(f"   ✓ Total Alerts: {filtered.get('total', 0)}")
        print(f"   ✓ Critical: {filtered.get('critical', 0)}")
        print(f"   ✓ High: {filtered.get('high', 0)}")
        
        if filtered != baseline:
            print(f"   ✓ PASS: Date filter is working! Values changed.")
        else:
            print(f"   ⚠ WARNING: Values are the same.")
    else:
        print(f"   ✗ Error: {response.status_code} - {response.text}")
    
    # Test stuck inventory
    print(f"\n3. Testing /api/v1/alerts/stuck-inventory WITH date filter:")
    response = requests.get(
        f"{BASE_URL}/api/v1/alerts/stuck-inventory",
        params={
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
    )
    if response.status_code == 200:
        alerts = response.json()
        print(f"   ✓ Retrieved {len(alerts)} stuck inventory alerts")
        if alerts:
            print(f"   ✓ Latest: {alerts[0].get('title')} - {alerts[0].get('severity')}")
    else:
        print(f"   ✗ Error: {response.status_code}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DATE FILTER VERIFICATION TEST")
    print("="*60)
    print(f"Testing against: {BASE_URL}")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}")
    
    try:
        # Test if server is running
        response = requests.get(f"{BASE_URL}/api/v1/alerts/summary")
        if response.status_code not in [200, 401]:  # 401 is OK (auth required)
            print(f"\n✗ ERROR: Cannot connect to backend at {BASE_URL}")
            print("  Make sure FastAPI server is running!")
            exit(1)
        
        # Run all tests
        test_executive_apis()
        test_leadtime_apis()
        test_alert_apis()
        
        print("\n" + "="*60)
        print("TEST COMPLETED")
        print("="*60)
        print("\nIf values changed with date filters, implementation is working ✓")
        print("If values stayed the same, all data might be within the filtered range.")
        
    except requests.exceptions.ConnectionError:
        print(f"\n✗ ERROR: Cannot connect to {BASE_URL}")
        print("  Make sure FastAPI server is running on port 8000!")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
