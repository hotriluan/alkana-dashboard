import requests
import json

# Test yield API endpoints
base_url = "http://localhost:8000/api/v1/yield"

print("=== TESTING YIELD API ENDPOINTS ===\n")

# Test 1: Summary
print("1. Testing /summary")
try:
    response = requests.get(f"{base_url}/summary")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Data: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 2: Records (first 10)
print("2. Testing /records (limit=10)")
try:
    response = requests.get(f"{base_url}/records?limit=10")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total records: {len(data)}")
        if data:
            print(f"\nFirst record:")
            print(json.dumps(data[0], indent=2))
            print(f"\nLast record:")
            print(json.dumps(data[-1], indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 3: By Plant
print("3. Testing /by-plant")
try:
    response = requests.get(f"{base_url}/by-plant")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Data: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 4: Top Performers
print("4. Testing /top-performers (limit=5)")
try:
    response = requests.get(f"{base_url}/top-performers?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total records: {len(data)}")
        if data:
            print(f"\nTop 3:")
            for i, record in enumerate(data[:3], 1):
                print(f"\n{i}. {record['material_description']}")
                print(f"   Yield: {record['yield_percentage']}%")
                print(f"   Input: {record['total_input_qty']} KG")
                print(f"   Output: {record['total_output_qty']} KG")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")
