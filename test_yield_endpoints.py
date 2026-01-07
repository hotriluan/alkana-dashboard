import requests
import json

# Test with correct base URL
base_url = "http://localhost:8000/api/v1"

print("=== TESTING YIELD ENDPOINTS ===\n")

# Test /yield/summary
print("1. GET /api/v1/yield/summary")
try:
    response = requests.get(f"{base_url}/yield/summary")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")

print("\n" + "="*60 + "\n")

# Test /yield/records with limit
print("2. GET /api/v1/yield/records?limit=5")
try:
    response = requests.get(f"{base_url}/yield/records?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total records returned: {len(data)}")
        if data:
            print(f"\nFirst record (lowest yield):")
            print(json.dumps(data[0], indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")

print("\n" + "="*60 + "\n")

# Test /yield/by-plant
print("3. GET /api/v1/yield/by-plant")
try:
    response = requests.get(f"{base_url}/yield/by-plant")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")

print("\n" + "="*60 + "\n")

# Test /yield/top-performers
print("4. GET /api/v1/yield/top-performers?limit=3")
try:
    response = requests.get(f"{base_url}/yield/top-performers?limit=3")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total records returned: {len(data)}")
        if data:
            for i, record in enumerate(data, 1):
                print(f"\n{i}. {record['material_description']}")
                print(f"   Material Code: {record['material_code']}")
                print(f"   Yield: {record['yield_percentage']}%")
                print(f"   Input: {record['total_input_qty']} KG")
                print(f"   Output: {record['total_output_qty']} KG")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")
