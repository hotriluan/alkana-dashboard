import requests
import json

# Login
login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    data={"username": "admin", "password": "admin123"}
)
token = login_response.json()["access_token"]
print(f"✅ Logged in, token: {token[:20]}...")

# Test executive summary
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/executive/summary", headers=headers)

print(f"\n=== Executive Summary Response ===")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
    
    # Calculate expected values
    total_ar = data.get('total_ar', 0)
    overdue_ar = data.get('overdue_ar', 0)
    overdue_pct = data.get('overdue_pct', 0)
    
    print(f"\n=== AR Metrics ===")
    print(f"Total AR: {total_ar:,.0f}")
    print(f"Overdue AR: {overdue_ar:,.0f}")
    print(f"Overdue %: {overdue_pct:.2f}%")
    print(f"\nExpected Overdue AR: 577,315,694")
    print(f"Expected Overdue %: {(577315694 / 45314939748 * 100):.2f}%")
else:
    print(response.text)
