"""
Debug Alert Monitor - No Data Issue

Skills: backend-development, databases
CLAUDE.md: KISS - Simple systematic debugging

Steps:
1. Check database - does fact_alerts have data?
2. Test backend API endpoints
3. Check frontend API calls
4. Verify data flow
"""
import sys
sys.path.insert(0, '.')

from src.db.connection import engine
from sqlalchemy import text
import requests

print("=" * 80)
print("ALERT MONITOR DEBUG - NO DATA ISSUE")
print("=" * 80)

# Step 1: Check Database
print("\n[STEP 1] DATABASE CHECK - fact_alerts table")
print("-" * 80)
try:
    result = engine.connect().execute(text("""
        SELECT 
            COUNT(*) as total_alerts,
            COUNT(CASE WHEN status='ACTIVE' THEN 1 END) as active_alerts,
            COUNT(CASE WHEN alert_type='STUCK_IN_TRANSIT' THEN 1 END) as stuck_alerts,
            COUNT(CASE WHEN alert_type='LOW_YIELD' THEN 1 END) as yield_alerts
        FROM fact_alerts
    """)).fetchone()
    
    print(f"Total alerts in DB: {result[0]}")
    print(f"Active alerts: {result[1]}")
    print(f"Stuck in transit: {result[2]}")
    print(f"Low yield: {result[3]}")
    
    if result[0] == 0:
        print("\n❌ PROBLEM FOUND: No alerts in database!")
        print("   Solution: Run ETL to generate alerts")
        print("   Command: python -m src.etl.main")
    else:
        print(f"\n✅ Database has {result[0]} alerts")
        
        # Show sample data
        print("\nSample alerts:")
        samples = engine.connect().execute(text("""
            SELECT id, alert_type, severity, message, status
            FROM fact_alerts
            LIMIT 3
        """)).fetchall()
        
        for s in samples:
            print(f"  - ID {s[0]}: {s[1]} ({s[2]}) - {s[4]}")
            
except Exception as e:
    print(f"❌ Database error: {e}")

# Step 2: Test Backend API Endpoints
print("\n[STEP 2] BACKEND API TEST")
print("-" * 80)

BASE_URL = "http://localhost:8000"

# Test 1: Summary endpoint
print("\nTesting GET /api/v1/alerts/summary")
try:
    response = requests.get(f"{BASE_URL}/api/v1/alerts/summary", timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data}")
        if data.get('total', 0) == 0:
            print("⚠️  API returns 0 alerts - check database or query logic")
        else:
            print(f"✅ API returns {data.get('total')} total alerts")
    else:
        print(f"❌ API error: {response.text}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend!")
    print("   Solution: Start backend with: uvicorn src.api.main:app --reload")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Stuck inventory endpoint
print("\nTesting GET /api/v1/alerts/stuck-inventory")
try:
    response = requests.get(f"{BASE_URL}/api/v1/alerts/stuck-inventory", timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {len(data)} alerts")
        if len(data) > 0:
            print(f"Sample: {data[0]}")
        else:
            print("⚠️  No stuck inventory alerts")
    else:
        print(f"❌ API error: {response.text}")
except requests.exceptions.ConnectionError:
    print("❌ Backend not running")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Low yield endpoint
print("\nTesting GET /api/v1/alerts/low-yield")
try:
    response = requests.get(f"{BASE_URL}/api/v1/alerts/low-yield", timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {len(data)} alerts")
        if len(data) > 0:
            print(f"Sample: {data[0]}")
        else:
            print("⚠️  No low yield alerts")
    else:
        print(f"❌ API error: {response.text}")
except requests.exceptions.ConnectionError:
    print("❌ Backend not running")
except Exception as e:
    print(f"❌ Error: {e}")

# Step 3: Check SQL Queries
print("\n[STEP 3] SQL QUERY VERIFICATION")
print("-" * 80)

print("\nTesting summary query:")
try:
    result = engine.connect().execute(text("""
        SELECT 
            COUNT(CASE WHEN severity='CRITICAL' THEN 1 END) as critical,
            COUNT(CASE WHEN severity='HIGH' THEN 1 END) as high,
            COUNT(CASE WHEN severity='MEDIUM' THEN 1 END) as medium,
            COUNT(*) as total
        FROM fact_alerts
        WHERE status = 'ACTIVE'
    """)).fetchone()
    
    print(f"Critical: {result[0]}, High: {result[1]}, Medium: {result[2]}, Total: {result[3]}")
    
    if result[3] == 0:
        print("⚠️  No ACTIVE alerts - check if all alerts are RESOLVED")
        
        # Check all statuses
        all_status = engine.connect().execute(text("""
            SELECT status, COUNT(*) 
            FROM fact_alerts 
            GROUP BY status
        """)).fetchall()
        
        print("\nAlert status breakdown:")
        for s in all_status:
            print(f"  {s[0]}: {s[1]} alerts")
            
except Exception as e:
    print(f"❌ Error: {e}")

# Summary
print("\n" + "=" * 80)
print("DIAGNOSIS SUMMARY")
print("=" * 80)

print("\n✅ CHECKLIST:")
print("[ ] Database has alerts in fact_alerts table")
print("[ ] Backend API is running (http://localhost:8000)")
print("[ ] API endpoints return data")
print("[ ] Frontend can connect to API")
print("[ ] Alerts have status='ACTIVE'")

print("\n💡 COMMON SOLUTIONS:")
print("1. No alerts in DB → Run ETL: python -m src.etl.main")
print("2. Backend not running → Start: uvicorn src.api.main:app --reload")
print("3. All alerts RESOLVED → Run ETL again to generate new alerts")
print("4. Frontend can't connect → Check CORS settings in src/api/main.py")

print("=" * 80)
