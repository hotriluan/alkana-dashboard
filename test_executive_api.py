import requests
from src.api.auth import create_access_token

# Create test token
token = create_access_token(data={"sub": "admin"})

# Test executive summary
response = requests.get(
    "http://localhost:8000/api/v1/dashboards/executive/summary",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text[:200]}")
if response.status_code == 200:
    print("Executive Summary Response:")
    print(response.json())
print("\n")

# Test revenue by division
response = requests.get(
    "http://localhost:8000/api/v1/dashboards/executive/revenue-by-division",
    headers={"Authorization": f"Bearer {token}"}
)

print("Revenue by Division:")
for item in response.json()[:3]:
    print(item)
