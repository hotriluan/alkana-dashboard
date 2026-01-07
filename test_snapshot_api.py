"""Test AR snapshot API after adding snapshot_date column"""
import requests

BASE_URL = "http://localhost:8000"

# Login
login_data = {"username": "admin", "password": "admin123"}
login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("TEST: AR Snapshot API")
print("=" * 60)

# Test snapshots endpoint
print("\n[1] GET /ar-aging/snapshots")
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/ar-aging/snapshots", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    snapshots = resp.json()
    print(f"Snapshots found: {len(snapshots)}")
    for snap in snapshots:
        print(f"  - {snap['snapshot_date']}: {snap['row_count']} rows")
else:
    print(f"Error: {resp.text}")

# Test summary with snapshot
print("\n[2] GET /ar-aging/summary (no snapshot_date)")
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/ar-aging/summary", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Total target: {data['total_target']:,.0f}")
    print(f"Total realization: {data['total_realization']:,.0f}")
    print(f"Divisions: {len(data['divisions'])}")
else:
    print(f"Error: {resp.text}")

print("\n✅ Test complete!")
