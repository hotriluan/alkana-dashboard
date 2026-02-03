#!/usr/bin/env python3
"""
Test Production API Endpoint

Calls production API to check inventory data
"""
import requests
import json
from getpass import getpass

# Production URL
PROD_URL = "https://alkanadashboard.com"

def test_production_api():
    """Test production inventory endpoint"""
    
    print("=" * 70)
    print("PRODUCTION API TEST")
    print("=" * 70)
    
    # Get credentials
    print(f"\nConnecting to: {PROD_URL}")
    username = input("Username [admin]: ").strip() or "admin"
    password = getpass("Password: ")
    
    # Login
    print("\n[1/3] Authenticating...")
    try:
        response = requests.post(
            f"{PROD_URL}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        print("✓ Authenticated")
    except Exception as e:
        print(f"✗ Login failed: {e}")
        return
    
    # Test inventory endpoint
    print("\n[2/3] Fetching inventory data...")
    try:
        response = requests.get(
            f"{PROD_URL}/api/v1/dashboards/inventory/top-movers-and-dead-stock",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 10, "category": "ALL_CORE"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        print("✓ API responded")
        
        # Analyze response
        print("\n[3/3] Analyzing data...")
        print(f"\nTop Movers: {len(data.get('top_movers', []))} items")
        if data.get('top_movers'):
            for i, item in enumerate(data['top_movers'][:3], 1):
                print(f"  {i}. {item['material_code'][:25]:25s} | "
                      f"Velocity: {item['velocity_score']:>5d} | "
                      f"Type: {item['material_type']}")
        
        print(f"\nDead Stock: {len(data.get('dead_stock', []))} items")
        if data.get('dead_stock'):
            for i, item in enumerate(data['dead_stock'][:3], 1):
                print(f"  {i}. {item['material_code'][:25]:25s} | "
                      f"Stock: {item['stock_kg']:>10,.0f} kg | "
                      f"Velocity: {item['velocity_score']:>3d}")
        
        # Check for issues
        print("\n" + "=" * 70)
        print("DIAGNOSIS")
        print("=" * 70)
        
        if not data.get('top_movers') and not data.get('dead_stock'):
            print("\n⚠️  WARNING: Both lists are empty!")
            if 'warning' in data:
                print(f"   API Warning: {data['warning']}")
            print("\n   Possible causes:")
            print("   1. Production database has no data")
            print("   2. Movement types don't match")
            print("   3. Date range has no data")
        elif data.get('top_movers') and all(m['velocity_score'] == 0 for m in data['top_movers']):
            print("\n⚠️  WARNING: All top movers have velocity = 0!")
            print("   This means no outbound movements found")
            print("   Check movement types in production database")
        else:
            print("\n✅ Data looks good!")
            print("   If dashboard still shows no bars:")
            print("   1. Check browser console for errors")
            print("   2. Try hard refresh (Ctrl+Shift+R)")
            print("   3. Check if frontend build is up to date")
        
        # Show full response
        print("\n" + "=" * 70)
        print("FULL API RESPONSE")
        print("=" * 70)
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
        
    except requests.exceptions.RequestException as e:
        print(f"✗ API request failed: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_production_api()
