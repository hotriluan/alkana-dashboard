"""
Simple fix: Re-upload ZRSD004 via Upload API to fill missing records
"""

import requests
from pathlib import Path

print("=" * 80)
print("🔄 HOTFIX: RE-UPLOADING ZRSD004 VIA API")
print("=" * 80)

# Check if FastAPI is running
api_url = "http://localhost:8000/api/v1/upload"
file_path = Path("demodata/zrsd004.XLSX")

try:
    print("\n📌 Uploading ZRSD004.XLSX via API...")
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(api_url, files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Upload successful!")
        print(f"  Upload ID: {data['upload_id']}")
        print(f"  Status: {data['status']}")
        print(f"  Message: {data['message']}")
        
        # Check status
        upload_id = data['upload_id']
        status_url = f"http://localhost:8000/api/v1/upload/{upload_id}/status"
        
        print(f"\n📌 Checking upload status...")
        status_response = requests.get(status_url)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"  Status: {status_data['status']}")
            print(f"  Loaded: {status_data['rows_loaded']:,}")
            print(f"  Updated: {status_data['rows_updated']:,}")
            print(f"  Skipped: {status_data['rows_skipped']:,}")
            print(f"  Failed: {status_data['rows_failed']:,}")
            
            if status_data['error_message']:
                print(f"  Error: {status_data['error_message']}")
        
        print("\n" + "=" * 80)
        print("✅ RE-UPLOAD COMPLETE!")
        print("=" * 80)
        print("\n📌 Now verify in dashboard:")
        print("  1. Open http://localhost:3000/lead-time")
        print("  2. Check if Planned Delivery Date is now populated")
        
    else:
        print(f"  ❌ Upload failed: {response.status_code}")
        print(f"  Response: {response.text}")

except requests.exceptions.ConnectionError:
    print(f"\n❌ ERROR: Cannot connect to API at {api_url}")
    print("  Please ensure FastAPI server is running:")
    print("  > python -m uvicorn src.main:app --reload")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
