"""Test AR Aging API with different snapshots"""
import requests
from datetime import date

API_URL = "http://localhost:8000/api/v1/dashboards/ar-aging/summary"

# Test with Jan 8 snapshot (101 records)
print("\n=== Testing Jan 8, 2026 (101 records) ===")
response1 = requests.get(API_URL, params={"snapshot_date": "2026-01-08"})
if response1.status_code == 200:
    data = response1.json()
    print(f"Total Target: {data['total_target']:,.0f}")
    print(f"Total Realization: {data['total_realization']:,.0f}")
    print(f"Collection Rate: {data['collection_rate_pct']}%")
    print(f"Report Date: {data['report_date']}")
else:
    print(f"❌ Error: {response1.status_code} - {response1.text}")

# Test with Jan 7 snapshot (98 records)
print("\n=== Testing Jan 7, 2026 (98 records) ===")
response2 = requests.get(API_URL, params={"snapshot_date": "2026-01-07"})
if response2.status_code == 200:
    data = response2.json()
    print(f"Total Target: {data['total_target']:,.0f}")
    print(f"Total Realization: {data['total_realization']:,.0f}")
    print(f"Collection Rate: {data['collection_rate_pct']}%")
    print(f"Report Date: {data['report_date']}")
else:
    print(f"❌ Error: {response2.status_code} - {response2.text}")

print("\n✅ If numbers are different, snapshot filtering works!")
