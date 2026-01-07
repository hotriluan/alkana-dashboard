"""
CLAUDE KIT: Sequential Thinking + Backend Development
Step-by-step verification of AR data pipeline
"""
import requests

BASE_URL = "http://localhost:8000"

# Login
login_data = {"username": "admin", "password": "admin123"}
login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 70)
print("CLAUDE KIT: AR DATA VERIFICATION")
print("Skills: Sequential Thinking, Backend Development, Database")
print("=" * 70)

# Step 1: Check database directly
print("\n[STEP 1] Database: Check fact_ar_aging records")
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://postgres:password123@localhost:5432/alkana_dashboard")

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            snapshot_date,
            COUNT(*) as row_count,
            SUM(total_target) as total_target,
            SUM(total_realization) as total_realization
        FROM fact_ar_aging
        WHERE snapshot_date IS NOT NULL
        GROUP BY snapshot_date
        ORDER BY snapshot_date DESC
    """)).fetchall()
    
    print(f"  Found {len(result)} snapshot(s)")
    for row in result:
        print(f"    {row[0]}: {row[1]} rows, Target: {row[2]:,.0f}, Realization: {row[3]:,.0f}")

# Step 2: Test snapshots API
print("\n[STEP 2] API: GET /ar-aging/snapshots")
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/ar-aging/snapshots", headers=headers)
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Response: {data}")
else:
    print(f"  Error: {resp.text}")

# Step 3: Test summary API (no snapshot - should return all data)
print("\n[STEP 3] API: GET /ar-aging/summary (no snapshot_date param)")
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/ar-aging/summary", headers=headers)
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Total Target: {data.get('total_target', 0):,.0f}")
    print(f"  Total Realization: {data.get('total_realization', 0):,.0f}")
    print(f"  Collection Rate: {data.get('collection_rate_pct', 0)}%")
    print(f"  Divisions: {len(data.get('divisions', []))}")
    for div in data.get('divisions', []):
        print(f"    - {div['division']}: {div['total_target']:,.0f}")
else:
    print(f"  Error: {resp.text}")

# Step 4: Test summary API with specific snapshot
print("\n[STEP 4] API: GET /ar-aging/summary?snapshot_date=2026-01-06")
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/ar-aging/summary?snapshot_date=2026-01-06", headers=headers)
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Total Target: {data.get('total_target', 0):,.0f}")
    print(f"  Total Realization: {data.get('total_realization', 0):,.0f}")
else:
    print(f"  Error: {resp.text}")

# Step 5: Check customers endpoint
print("\n[STEP 5] API: GET /ar-aging/customers")
resp = requests.get(f"{BASE_URL}/api/v1/dashboards/ar-aging/customers?limit=5", headers=headers)
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"  Customers returned: {len(data)}")
    for i, cust in enumerate(data[:3], 1):
        print(f"    {i}. {cust.get('customer_name', 'N/A')}: {cust.get('total_target', 0):,.0f}")
else:
    print(f"  Error: {resp.text}")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
