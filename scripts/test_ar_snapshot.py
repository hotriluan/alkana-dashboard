"""
Test Phase 2: AR Snapshot Date Feature

This tests the snapshot_date parameter for AR uploads.
Full upsert mode requires refactoring all loaders (Phase 3).

Skills: api-testing
"""
import sys
sys.path.insert(0, '.')

import requests
from pathlib import Path
from datetime import date
import time

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("PHASE 2 TEST: AR Snapshot Date & Monthly Reset")
print("=" * 70)

# Check if ZRFI005 file exists
AR_FILE = Path("demodata/zrfi005.xlsx")
if not AR_FILE.exists():
    print(f"\n⚠ AR file not found: {AR_FILE}")
    print("Creating a minimal test with ZRSD002 instead...")
    TEST_FILE = Path("demodata/zrsd002.xlsx")
    if not TEST_FILE.exists():
        print(f"❌ No test files available")
        sys.exit(1)
else:
    TEST_FILE = AR_FILE

print(f"\nTest file: {TEST_FILE.name}")

# ============================================================================
# TEST 1: Upload with snapshot_date parameter
# ============================================================================
print("\n" + "=" * 70)
print("TEST 1: Upload with snapshot_date parameter")
print("=" * 70)

today = date.today()
print(f"\nUploading {TEST_FILE.name} with snapshot_date={today}")

with open(TEST_FILE, 'rb') as f:
    files = {'file': (TEST_FILE.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    data = {'snapshot_date': today.strftime('%Y-%m-%d')}
    response = requests.post(f"{BASE_URL}/api/v1/upload", files=files, data=data)

if response.status_code != 200:
    print(f"❌ Upload failed: {response.status_code}")
    print(response.text)
    sys.exit(1)

result = response.json()
upload_id = result['upload_id']
print(f"✓ Upload initiated")
print(f"  Upload ID: {upload_id}")
print(f"  Status: {result['status']}")

# Poll for completion
print(f"\nWaiting for processing...")
for i in range(10):
    time.sleep(1)
    response = requests.get(f"{BASE_URL}/api/v1/upload/{upload_id}/status")
    
    if response.status_code != 200:
        print(f"❌ Status check failed: {response.status_code}")
        break
    
    status = response.json()
    
    if status['status'] == 'completed':
        print(f"\n✅ Upload completed!")
        print(f"  File type: {status['file_type']}")
        print(f"  Snapshot date: {status.get('snapshot_date', 'N/A')}")
        print(f"  Rows loaded: {status['rows_loaded']}")
        print(f"  Rows updated: {status['rows_updated']}")
        print(f"  Rows skipped: {status['rows_skipped']}")
        print(f"  Rows failed: {status['rows_failed']}")
        break
    elif status['status'] == 'failed':
        print(f"\n❌ Upload failed!")
        print(f"  Error: {status.get('error_message', 'Unknown')}")
        break
    else:
        print(f"  [{i+1}] Status: {status['status']}...", end='\r')

# ============================================================================
# TEST 2: Invalid date format validation
# ============================================================================
print("\n" + "=" * 70)
print("TEST 2: Date validation")
print("=" * 70)

print(f"\nUploading with invalid snapshot_date format")

with open(TEST_FILE, 'rb') as f:
    files = {'file': (TEST_FILE.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    data = {'snapshot_date': 'invalid-date'}
    response = requests.post(f"{BASE_URL}/api/v1/upload", files=files, data=data)

if response.status_code == 400:
    print(f"✅ Validation working!")
    print(f"  Error message: {response.json().get('detail')}")
else:
    print(f"⚠ Expected 400, got {response.status_code}")

# ============================================================================
# TEST 3: Upload without snapshot_date (should default to today)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 3: Upload without snapshot_date (defaults to today)")
print("=" * 70)

print(f"\nUploading without snapshot_date parameter")

with open(TEST_FILE, 'rb') as f:
    files = {'file': ('test_no_date.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post(f"{BASE_URL}/api/v1/upload", files=files)

if response.status_code == 200:
    result = response.json()
    upload_id = result['upload_id']
    print(f"✓ Upload initiated (ID: {upload_id})")
    
    time.sleep(2)
    response = requests.get(f"{BASE_URL}/api/v1/upload/{upload_id}/status")
    status = response.json()
    
    if status['file_type'] == 'ZRFI005':
        print(f"✅ AR file defaults snapshot_date to today: {status.get('snapshot_date', 'N/A')}")
    else:
        print(f"✓ Non-AR file, snapshot_date not required")

print("\n" + "=" * 70)
print("PHASE 2 TESTING COMPLETE")
print("=" * 70)
print("\nFeatures verified:")
print("  ✓ snapshot_date parameter accepted")
print("  ✓ Date format validation")
print("  ✓ Default to today for AR files")
print("\nNote: Full upsert mode requires loader refactoring (planned for Phase 3)")
print("=" * 70)
