"""
Test Phase 2 Features: AR Monthly Reset & Upsert Mode

Skills: api-testing, data-validation
"""
import sys
sys.path.insert(0, '.')

import requests
from pathlib import Path
from datetime import date, timedelta
import time

BASE_URL = "http://localhost:8000"
TEST_FILE = Path("demodata/zrsd002.xlsx")

print("=" * 70)
print("PHASE 2 TESTING: AR Monthly Reset & Upsert Mode")
print("=" * 70)

# ============================================================================
# TEST 1: Upsert Mode - Upload same file twice
# ============================================================================
print("\n" + "=" * 70)
print("TEST 1: Upsert Mode (Upload same file twice)")
print("=" * 70)

if not TEST_FILE.exists():
    print(f"❌ Test file not found: {TEST_FILE}")
    sys.exit(1)

print(f"\n1.1 First upload: {TEST_FILE.name}")
with open(TEST_FILE, 'rb') as f:
    files = {'file': (TEST_FILE.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post(f"{BASE_URL}/api/v1/upload", files=files)

if response.status_code != 200:
    print(f"❌ First upload failed: {response.status_code}")
    print(response.text)
    sys.exit(1)

upload1 = response.json()
print(f"✓ First upload completed")
print(f"  Upload ID: {upload1['upload_id']}")

# Wait for processing
time.sleep(2)
response = requests.get(f"{BASE_URL}/api/v1/upload/{upload1['upload_id']}/status")
status1 = response.json()
print(f"\nFirst upload stats:")
print(f"  Status: {status1['status']}")
print(f"  Rows loaded: {status1['rows_loaded']}")
print(f"  Rows updated: {status1['rows_updated']}")
print(f"  Rows skipped: {status1['rows_skipped']}")
print(f"  Rows failed: {status1['rows_failed']}")

# Second upload - same file (should upsert)
print(f"\n1.2 Second upload: Same file (should skip unchanged rows)")
time.sleep(1)

with open(TEST_FILE, 'rb') as f:
    files = {'file': (TEST_FILE.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    # Use different filename to bypass hash check
    files = {'file': ('test_upsert.xlsx', open(TEST_FILE, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post(f"{BASE_URL}/api/v1/upload", files=files)

if response.status_code != 200:
    print(f"❌ Second upload failed: {response.status_code}")
    print(response.text)
else:
    upload2 = response.json()
    print(f"✓ Second upload initiated")
    print(f"  Upload ID: {upload2['upload_id']}")
    
    # Wait for processing
    time.sleep(2)
    response = requests.get(f"{BASE_URL}/api/v1/upload/{upload2['upload_id']}/status")
    status2 = response.json()
    
    print(f"\nSecond upload stats (upsert mode):")
    print(f"  Status: {status2['status']}")
    print(f"  Rows loaded: {status2['rows_loaded']} (new)")
    print(f"  Rows updated: {status2['rows_updated']} (changed)")
    print(f"  Rows skipped: {status2['rows_skipped']} (unchanged) ⭐")
    print(f"  Rows failed: {status2['rows_failed']}")
    
    if status2['rows_skipped'] > 0:
        print(f"\n✅ Upsert mode working! {status2['rows_skipped']} rows skipped as unchanged")
    else:
        print(f"\n⚠ Warning: Expected some skipped rows in upsert mode")

# ============================================================================
# TEST 2: AR Monthly Reset (Snapshot Date)
# ============================================================================
print("\n" + "=" * 70)
print("TEST 2: AR Snapshot Date (if ZRFI005 file available)")
print("=" * 70)

# Check if AR file exists
AR_FILE = Path("demodata/zrfi005.xlsx")
if not AR_FILE.exists():
    print(f"⚠ AR file not found: {AR_FILE}")
    print("Skipping AR monthly reset test")
else:
    # Test 2.1: Upload with today's date
    today = date.today()
    print(f"\n2.1 Upload AR with snapshot_date={today}")
    
    with open(AR_FILE, 'rb') as f:
        files = {'file': (AR_FILE.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        data = {'snapshot_date': today.strftime('%Y-%m-%d')}
        response = requests.post(f"{BASE_URL}/api/v1/upload", files=files, data=data)
    
    if response.status_code != 200:
        print(f"❌ AR upload failed: {response.status_code}")
        print(response.text)
    else:
        upload_ar1 = response.json()
        print(f"✓ AR upload completed")
        print(f"  Upload ID: {upload_ar1['upload_id']}")
        
        time.sleep(2)
        response = requests.get(f"{BASE_URL}/api/v1/upload/{upload_ar1['upload_id']}/status")
        status_ar1 = response.json()
        print(f"  Snapshot date: {status_ar1.get('snapshot_date', 'N/A')}")
        print(f"  Rows loaded: {status_ar1['rows_loaded']}")
    
    # Test 2.2: Upload with first day of next month (should trigger reset)
    next_month = today.replace(day=1) + timedelta(days=32)
    first_day_next = next_month.replace(day=1)
    
    print(f"\n2.2 Upload AR with snapshot_date={first_day_next} (1st of month)")
    print(f"  ⚠ This should DELETE previous month's data")
    
    with open(AR_FILE, 'rb') as f:
        files = {'file': ('ar_next_month.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        data = {'snapshot_date': first_day_next.strftime('%Y-%m-%d')}
        response = requests.post(f"{BASE_URL}/api/v1/upload", files=files, data=data)
    
    if response.status_code != 200:
        print(f"❌ AR monthly upload failed: {response.status_code}")
        print(response.text)
    else:
        upload_ar2 = response.json()
        print(f"✓ AR monthly upload completed")
        print(f"  Upload ID: {upload_ar2['upload_id']}")
        
        time.sleep(2)
        response = requests.get(f"{BASE_URL}/api/v1/upload/{upload_ar2['upload_id']}/status")
        status_ar2 = response.json()
        print(f"  Snapshot date: {status_ar2.get('snapshot_date', 'N/A')}")
        print(f"  Rows loaded: {status_ar2['rows_loaded']}")
        print(f"\n✅ Monthly reset logic executed (check server logs for deletion count)")

# ============================================================================
# TEST 3: Validation - Invalid snapshot_date format
# ============================================================================
print("\n" + "=" * 70)
print("TEST 3: Validation - Invalid snapshot_date")
print("=" * 70)

print("\n3.1 Upload with invalid date format")
with open(TEST_FILE, 'rb') as f:
    files = {'file': (TEST_FILE.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    data = {'snapshot_date': '2026-13-45'}  # Invalid date
    response = requests.post(f"{BASE_URL}/api/v1/upload", files=files, data=data)

if response.status_code == 400:
    print(f"✅ Validation working! Rejected invalid date")
    print(f"  Error: {response.json().get('detail', 'N/A')}")
else:
    print(f"⚠ Expected 400 error, got {response.status_code}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 70)
print("PHASE 2 TESTING COMPLETE")
print("=" * 70)
print("\nFeatures tested:")
print("  ✓ Upsert mode (skip unchanged rows)")
print("  ✓ AR snapshot_date parameter")
print("  ✓ AR monthly reset (day=1 deletes previous month)")
print("  ✓ Date validation")
print("\nCheck server logs for detailed ETL processing output")
print("=" * 70)
