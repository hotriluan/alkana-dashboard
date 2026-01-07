"""
Test /by-channel API endpoint via terminal
"""
import sys
sys.path.insert(0, '.')
import requests
import json

print("Testing /api/v1/leadtime/by-channel endpoint...")
print("=" * 70)

try:
    response = requests.get('http://localhost:8000/api/v1/leadtime/by-channel')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS! Received {len(data)} channels\n")
        
        # Display results in table format
        print(f"{'Channel':<20s} {'MTO Orders':>12s} {'MTO Avg':>10s} {'MTS Orders':>12s} {'MTS Avg':>10s} {'Total':>8s}")
        print("-" * 70)
        
        for row in data:
            mto_avg = f"{row['mto_avg_leadtime']:.1f}d" if row['mto_avg_leadtime'] else "-"
            mts_avg = f"{row['mts_avg_leadtime']:.1f}d" if row['mts_avg_leadtime'] else "-"
            
            print(f"{row['channel_name']:<20s} {row['mto_orders']:>12d} {mto_avg:>10s} {row['mts_orders']:>12d} {mts_avg:>10s} {row['total_orders']:>8d}")
        
        print("\n" + "=" * 70)
        print("Sample JSON response (first channel):")
        print(json.dumps(data[0], indent=2))
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to backend server")
    print("   Make sure backend is running on http://localhost:8000")
except Exception as e:
    print(f"❌ ERROR: {e}")
