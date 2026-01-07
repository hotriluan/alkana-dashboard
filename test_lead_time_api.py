from fastapi.testclient import TestClient
from src.api.main import app
import json

client = TestClient(app)

def test_endpoint(url):
    print(f"\n--- Testing {url} ---")
    try:
        response = client.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

print("=== LEAD TIME API VERIFICATION ===")

# 1. Summary
test_endpoint("/api/v1/leadtime/summary")

# 2. Breakdown
test_endpoint("/api/v1/leadtime/breakdown")

# 3. Orders
test_endpoint("/api/v1/leadtime/orders?limit=3")
