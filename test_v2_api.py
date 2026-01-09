"""Test V2 Yield API endpoint"""
import requests
from datetime import date

API_URL = "http://localhost:8000/api/v2/yield/variance"

print("=== Testing V2 Yield Variance API ===\n")

# Test 1: Basic query (last 30 days)
print("Test 1: Basic query")
response = requests.get(API_URL)
if response.status_code == 200:
    data = response.json()
    print(f"✓ Status: {response.status_code}")
    print(f"  Total orders: {data['summary']['total_orders']}")
    print(f"  Total loss: {data['summary']['total_loss_kg']:,.2f} kg")
    print(f"  Avg loss %: {data['summary']['avg_loss_pct']:.2f}%")
    print(f"  Records: {len(data['records'])}")
    print(f"  Date range: {data['date_range']}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

# Test 2: Filter by date
print("\nTest 2: Filter by date (2026-01-08)")
response2 = requests.get(API_URL, params={
    "start_date": "2026-01-08",
    "end_date": "2026-01-08"
})
if response2.status_code == 200:
    data2 = response2.json()
    print(f"✓ Status: {response2.status_code}")
    print(f"  Records for 2026-01-08: {len(data2['records'])}")
    if data2['records']:
        sample = data2['records'][0]
        print(f"  Sample: Order {sample['process_order_id']}, Loss: {sample['loss_pct']}%")
else:
    print(f"❌ Error: {response2.status_code}")

# Test 3: Filter by loss threshold
print("\nTest 3: High loss filter (>10%)")
response3 = requests.get(API_URL, params={
    "loss_threshold": 10
})
if response3.status_code == 200:
    data3 = response3.json()
    print(f"✓ Status: {response3.status_code}")
    print(f"  High loss records: {len(data3['records'])}")
else:
    print(f"❌ Error: {response3.status_code}")

print("\n✅ API testing complete")
