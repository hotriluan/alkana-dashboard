"""
Test script to verify MTO completion trend endpoint
Tests different date ranges to ensure dynamic X-axis formatting
"""
from datetime import datetime, timedelta
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/dashboards/mto-orders"

def test_completion_trend():
    print("=== TESTING MTO COMPLETION TREND ENDPOINT ===\n")
    
    # Test 1: Full Year (should show monthly - Jan to Dec)
    print("TEST 1: Full Year (2025-01-01 to 2025-12-31)")
    print("Expected: Monthly aggregation (Jan, Feb, Mar...)")
    try:
        response = requests.get(
            f"{BASE_URL}/completion-trend",
            params={"start_date": "2025-01-01", "end_date": "2025-12-31"},
            headers={"Authorization": "Bearer test"}  # Adjust if auth needed
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Got {len(data)} periods")
            print(f"  First 3: {[d['period'] for d in data[:3]]}")
            print(f"  Sample data: {json.dumps(data[0], indent=2)}")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Q4 (should show monthly - Oct, Nov, Dec)
    print("TEST 2: Q4 2025 (2025-10-01 to 2025-12-31)")
    print("Expected: Monthly aggregation (Oct, Nov, Dec)")
    try:
        response = requests.get(
            f"{BASE_URL}/completion-trend",
            params={"start_date": "2025-10-01", "end_date": "2025-12-31"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Got {len(data)} periods")
            print(f"  Periods: {[d['period'] for d in data]}")
        else:
            print(f"✗ Failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 3: Current Month (should show weekly - DD/MM format)
    today = datetime.now()
    first_day = today.replace(day=1).strftime("%Y-%m-%d")
    last_day = today.strftime("%Y-%m-%d")
    
    print(f"TEST 3: Current Month ({first_day} to {last_day})")
    print("Expected: Weekly aggregation (DD/MM format)")
    try:
        response = requests.get(
            f"{BASE_URL}/completion-trend",
            params={"start_date": first_day, "end_date": last_day}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Got {len(data)} periods")
            if data:
                print(f"  Periods: {[d['period'] for d in data]}")
        else:
            print(f"✗ Failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 4: Default (no params - should use current month)
    print("TEST 4: Default (no date params)")
    print("Expected: Current month with weekly aggregation")
    try:
        response = requests.get(f"{BASE_URL}/completion-trend")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Got {len(data)} periods")
            if data:
                print(f"  Periods: {[d['period'] for d in data]}")
        else:
            print(f"✗ Failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("\n⚠️  Make sure the API server is running at http://localhost:8000\n")
    test_completion_trend()
    print("\n✅ All tests completed!\n")
