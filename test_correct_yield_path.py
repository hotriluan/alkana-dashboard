import requests
import json

# Test with CORRECT path (double prefix)
base_url = "http://localhost:8000/api/v1/dashboards/yield"

print("=== TESTING WITH CORRECT PATH ===\n")
print(f"Base URL: {base_url}\n")

# Test summary
print("1. GET /api/v1/dashboards/yield/summary")
try:
    response = requests.get(f"{base_url}/summary")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test records
print("2. GET /api/v1/dashboards/yield/records?limit=5")
try:
    response = requests.get(f"{base_url}/records?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Records returned: {len(data)}")
        if data:
            print(f"\nFirst record:")
            print(json.dumps(data[0], indent=2))
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
