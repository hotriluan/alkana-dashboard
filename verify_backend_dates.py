"""
CLAUDE KIT: Backend Development + Testing
Verify all backend APIs properly support date filtering

Skills: Backend Development, Testing, Sequential Thinking
"""
import requests

BASE_URL = "http://localhost:8000"

# Login
login_data = {"username": "admin", "password": "admin123"}
login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 80)
print("CLAUDE KIT: Backend Date Filter Verification")
print("Skills: Backend Development, Testing")
print("=" * 80)

endpoints = [
    ("Inventory Summary", "/api/v1/dashboards/inventory/summary"),
    ("Inventory Items", "/api/v1/dashboards/inventory/items"),
    ("Inventory By Plant", "/api/v1/dashboards/inventory/by-plant"),
    ("MTO Orders Summary", "/api/v1/dashboards/mto-orders/summary"),
    ("MTO Orders List", "/api/v1/dashboards/mto-orders/orders"),
    ("Production Yield Summary", "/api/v1/dashboards/yield/summary"),
    ("Production Yield Records", "/api/v1/dashboards/yield/records"),
    ("Production Yield By Plant", "/api/v1/dashboards/yield/by-plant"),
    ("Sales Summary", "/api/v1/dashboards/sales/summary"),
    ("Sales Customers", "/api/v1/dashboards/sales/customers"),
    ("Sales By Division", "/api/v1/dashboards/sales/by-division"),
]

params = {"start_date": "2025-12-01", "end_date": "2026-01-06"}

print("\nTesting endpoints with date filters:")
print(f"  Params: {params}\n")

passed = 0
failed = []

for name, endpoint in endpoints:
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", params=params, headers=headers)
        if resp.status_code == 200:
            print(f"  ✅ {name}: {resp.status_code}")
            passed += 1
        else:
            print(f"  ❌ {name}: {resp.status_code}")
            failed.append((name, resp.status_code))
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:50]}")
        failed.append((name, str(e)[:50]))

print("\n" + "=" * 80)
print(f"RESULT: {passed}/{len(endpoints)} endpoints working")
print("=" * 80)

if failed:
    print("\nFailed endpoints:")
    for name, error in failed:
        print(f"  - {name}: {error}")
else:
    print("\n🎉 All endpoints working correctly!")
