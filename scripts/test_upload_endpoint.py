"""
Test upload endpoint with sample file

Skills: api-testing, file-operations
"""
import sys
sys.path.insert(0, '.')

import requests
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"
TEST_FILE = Path("demodata/zrsd002.xlsx")

print("=" * 60)
print("TEST: Upload Endpoint")
print("=" * 60)

# Check if file exists
if not TEST_FILE.exists():
    print(f"❌ Test file not found: {TEST_FILE}")
    sys.exit(1)

print(f"\n1. Uploading file: {TEST_FILE}")
print(f"   File size: {TEST_FILE.stat().st_size:,} bytes")

# Upload file
with open(TEST_FILE, 'rb') as f:
    files = {'file': (TEST_FILE.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post(f"{BASE_URL}/api/v1/upload", files=files)

if response.status_code != 200:
    print(f"❌ Upload failed: {response.status_code}")
    print(response.text)
    sys.exit(1)

upload_result = response.json()
print(f"✓ Upload initiated")
print(f"  Upload ID: {upload_result['upload_id']}")
print(f"  File type detected: {upload_result.get('file_type', 'N/A')}")
print(f"  Status: {upload_result['status']}")

# Check status
upload_id = upload_result['upload_id']
print(f"\n2. Checking status...")

for i in range(10):  # Poll for 10 seconds
    response = requests.get(f"{BASE_URL}/api/v1/upload/{upload_id}/status")
    
    if response.status_code != 200:
        print(f"❌ Status check failed: {response.status_code}")
        break
    
    status_result = response.json()
    print(f"   [{i+1}] Status: {status_result['status']}")
    
    if status_result['status'] == 'completed':
        print(f"\n✓ Processing completed!")
        print(f"  Rows loaded: {status_result['rows_loaded']}")
        print(f"  Rows updated: {status_result['rows_updated']}")
        print(f"  Rows skipped: {status_result['rows_skipped']}")
        print(f"  Rows failed: {status_result['rows_failed']}")
        break
    
    if status_result['status'] == 'failed':
        print(f"\n❌ Processing failed!")
        print(f"  Error: {status_result.get('error_message', 'Unknown error')}")
        break
    
    time.sleep(1)

# Get upload history
print(f"\n3. Fetching upload history...")
response = requests.get(f"{BASE_URL}/api/v1/upload/history?limit=5")

if response.status_code == 200:
    history = response.json()
    print(f"✓ Recent uploads: {len(history)}")
    for item in history[:3]:
        print(f"  - {item['original_name']} ({item['file_type']}) - {item['status']}")
else:
    print(f"❌ History fetch failed: {response.status_code}")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
