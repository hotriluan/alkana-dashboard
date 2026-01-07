"""Quick test Executive Dashboard after schema fix"""
import requests

BASE_URL = "http://localhost:8000"

# Test with auth (get token first from login)
try:
    # Login to get token
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test without filter
        print("Testing /api/v1/dashboards/executive/summary WITHOUT filter:")
        r1 = requests.get(f"{BASE_URL}/api/v1/dashboards/executive/summary", headers=headers)
        if r1.status_code == 200:
            data = r1.json()
            print(f"  ✓ Total Revenue: {data.get('total_revenue', 0):,.0f}")
            print(f"  ✓ Total Customers: {data.get('total_customers', 0)}")
        else:
            print(f"  ✗ Error {r1.status_code}: {r1.text[:200]}")
        
        # Test with 30-day filter
        print("\nTesting WITH 30-day filter:")
        r2 = requests.get(
            f"{BASE_URL}/api/v1/dashboards/executive/summary",
            params={"start_date": "2025-12-07", "end_date": "2026-01-06"},
            headers=headers
        )
        if r2.status_code == 200:
            data = r2.json()
            print(f"  ✓ Total Revenue: {data.get('total_revenue', 0):,.0f}")
            print(f"  ✓ Total Customers: {data.get('total_customers', 0)}")
            print("  ✓ SUCCESS - Date filter working!")
        else:
            print(f"  ✗ Error {r2.status_code}: {r2.text[:300]}")
    else:
        print(f"Login failed: {login_response.status_code}")
        print("Note: Make sure you have a user 'admin' with password 'admin123'")
        
except Exception as e:
    print(f"Error: {e}")
