"""Trigger transform via API endpoint"""
import requests

BASE_URL = "http://localhost:8000"

# Login
login_data = {"username": "admin", "password": "admin123"}
login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 70)
print("CLAUDE KIT: Trigger AR Transform via API")
print("=" * 70)

# Trigger transform
print("\nPOST /admin/transform")
resp = requests.post(f"{BASE_URL}/api/v1/admin/transform", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"Response: {resp.json()}")
else:
    print(f"Error: {resp.text}")

# Verify result
print("\nVerifying fact_ar_aging...")
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://postgres:password123@localhost:5432/alkana_dashboard")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            snapshot_date,
            COUNT(*) as rows,
            SUM(total_target) as target
        FROM fact_ar_aging
        GROUP BY snapshot_date
    """)).fetchall()
    
    print(f"fact_ar_aging: {len(result)} snapshots")
    for row in result:
        print(f"  {row[0]}: {row[1]} rows, Target: {row[2]:,.0f}")

print("\n✅ Done")
