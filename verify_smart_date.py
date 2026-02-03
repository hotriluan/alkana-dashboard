#!/usr/bin/env python3
"""
Smart Date Range - Quick Verification Script

Tests the new /latest-data-date endpoint to verify smart date fallback logic.
Run from project root: python verify_smart_date.py
"""
import requests
from datetime import date

API_BASE = "http://localhost:8000"
USERNAME = "admin"  # Update with your credentials
PASSWORD = "admin123"  # Update with your credentials


def get_token():
    """Login and get JWT token"""
    response = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        data={"username": USERNAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.text}")


def test_latest_data_date(token):
    """Test the new latest-data-date endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Testing Smart Date Range Endpoint...")
    print("=" * 60)
    
    response = requests.get(
        f"{API_BASE}/api/v1/dashboards/executive/latest-data-date",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    
    print(f"\n✅ API Response Successful")
    print(f"\n📊 Latest Data Dates:")
    print(f"   • Billing:    {data['latest_billing_date']}")
    print(f"   • Inventory:  {data['latest_inventory_date']}")
    print(f"   • Production: {data['latest_production_date']}")
    
    print(f"\n📅 Recommended Date Range:")
    print(f"   • Start: {data['recommended_start_date']}")
    print(f"   • End:   {data['recommended_end_date']}")
    
    print(f"\n🎯 Current Month Data Available: {'YES ✅' if data['has_current_month_data'] else 'NO ❌'}")
    
    # Verify logic
    today = date.today()
    current_month_start = date(today.year, today.month, 1).strftime('%Y-%m-%d')
    
    if not data['has_current_month_data']:
        print(f"\n✅ SMART FALLBACK ACTIVE:")
        print(f"   Current month ({current_month_start}) has no data.")
        print(f"   Dashboard will default to: {data['recommended_start_date']} - {data['recommended_end_date']}")
    else:
        print(f"\n✅ CURRENT MONTH HAS DATA:")
        print(f"   Dashboard will use current month: {current_month_start} - {today.strftime('%Y-%m-%d')}")
    
    print("\n" + "=" * 60)


def main():
    print("\n🚀 Smart Date Range Verification")
    print("=" * 60)
    
    try:
        # Step 1: Login
        print("\n1️⃣  Logging in...")
        token = get_token()
        print("   ✅ Login successful")
        
        # Step 2: Test smart date endpoint
        print("\n2️⃣  Testing smart date range endpoint...")
        test_latest_data_date(token)
        
        print("\n\n✅ VERIFICATION COMPLETE")
        print("\nNext Steps:")
        print("  1. Start frontend: cd web && npm run dev")
        print("  2. Open browser: http://localhost:5173")
        print("  3. Navigate to Executive Dashboard")
        print("  4. Verify date picker shows recommended range (not current month)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("  • Ensure backend is running: cd src && uvicorn api.main:app --reload")
        print("  • Check credentials in this script")
        print("  • Verify database has data")


if __name__ == "__main__":
    main()
