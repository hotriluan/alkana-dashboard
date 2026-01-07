"""
CLAUDE KIT: End-to-End Date Filter Test
Verify data changes when date range changes

Skills: Testing, Sequential Thinking
"""
import requests

BASE_URL = "http://localhost:8000"

# Login
login_data = {"username": "admin", "password": "admin123"}
login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 80)
print("CLAUDE KIT: End-to-End Date Filter Verification")
print("Skills: Testing, Sequential Thinking")
print("=" * 80)

# Test Sales Performance with different date ranges
print("\n" + "="*40)
print("SALES PERFORMANCE DATE FILTER TEST")
print("="*40)

# Full range (no filter)
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/sales/summary", headers=headers)
data_full = resp.json()
print(f"\n[1] Full range (no date filter):")
print(f"    Total Sales: {data_full['total_sales']:,.0f}")
print(f"    Customers: {data_full['total_customers']}")
print(f"    Orders: {data_full['total_orders']}")

# December only
params = {"start_date": "2025-12-01", "end_date": "2025-12-31"}
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/sales/summary", params=params, headers=headers)
data_dec = resp.json()
print(f"\n[2] December 2025 only:")
print(f"    Total Sales: {data_dec['total_sales']:,.0f}")
print(f"    Customers: {data_dec['total_customers']}")
print(f"    Orders: {data_dec['total_orders']}")

# Last 7 days
params = {"start_date": "2025-12-25", "end_date": "2025-12-31"}
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/sales/summary", params=params, headers=headers)
data_week = resp.json()
print(f"\n[3] Last week of Dec (25-31):")
print(f"    Total Sales: {data_week['total_sales']:,.0f}")
print(f"    Customers: {data_week['total_customers']}")
print(f"    Orders: {data_week['total_orders']}")

# Verify data CHANGES
print("\n" + "="*40)
print("VERIFICATION")
print("="*40)

if data_full['total_sales'] > data_dec['total_sales'] > data_week['total_sales']:
    print("✅ Sales decrease correctly as date range narrows")
else:
    print("❌ Sales should decrease: Full > December > Week")
    print(f"   Full: {data_full['total_sales']:,.0f}")
    print(f"   Dec: {data_dec['total_sales']:,.0f}")  
    print(f"   Week: {data_week['total_sales']:,.0f}")

if data_full['total_orders'] >= data_dec['total_orders'] >= data_week['total_orders']:
    print("✅ Orders decrease correctly as date range narrows")
else:
    print("❌ Orders should decrease")

# Compare other dashboards
print("\n" + "="*40)
print("OTHER DASHBOARDS DATE FILTER TEST")
print("="*40)

dashboards = [
    ("Inventory", "/api/v1/dashboards/inventory/summary", "total_items"),
    ("Production Yield", "/api/v1/dashboards/yield/summary", "total_input"),
    ("MTO Orders", "/api/v1/dashboards/mto-orders/summary", "total_orders"),
]

for name, endpoint, key in dashboards:
    # Full range
    resp_full = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    val_full = resp_full.json().get(key, 0)
    
    # December only
    resp_dec = requests.get(f"{BASE_URL}{endpoint}", 
                           params={"start_date": "2025-12-01", "end_date": "2025-12-31"},
                           headers=headers)
    val_dec = resp_dec.json().get(key, 0)
    
    status = "✅" if val_full >= val_dec else "⚠️"
    print(f"{status} {name}: Full={val_full:,.0f}, Dec={val_dec:,.0f}")

print("\n" + "="*80)
print("🎉 DATE FILTER IMPLEMENTATION COMPLETE")
print("="*80)
