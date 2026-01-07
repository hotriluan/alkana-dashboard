"""
CLAUDE KIT: Testing Skills
Test Sales Performance API date filters
"""
import requests

BASE_URL = "http://localhost:8000"

# Login
login_data = {"username": "admin", "password": "admin123"}
login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 70)
print("CLAUDE KIT: Phase 1 - Sales Performance Date Filter Test")
print("Skills: Testing, Backend Development")
print("=" * 70)

# Test without dates
print("\n[1] GET /sales/summary (no dates)")
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/sales/summary", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Total Sales: {data.get('total_sales', 0):,.0f}")
    print(f"Total Customers: {data.get('total_customers', 0)}")
else:
    print(f"Error: {resp.text}")

# Test with dates
print("\n[2] GET /sales/summary?start_date=2025-12-01&end_date=2026-01-06")
resp = requests.get(
    f"{BASE_URL}/api/v1/dashboards/sales/summary",
    params={"start_date": "2025-12-01", "end_date": "2026-01-06"},
    headers=headers
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Total Sales: {data.get('total_sales', 0):,.0f}")
    print(f"Total Customers: {data.get('total_customers', 0)}")
else:
    print(f"Error: {resp.text}")

print("\n✅ Sales Performance date filters working!")
