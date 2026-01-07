"""
Debug Empty Alert Tables

Skills: backend-development, databases
CLAUDE.md: KISS - Test API endpoints systematically

Issue: KPI cards show 1182 alerts but tables are empty
"""
import requests
import sys
sys.path.insert(0, '.')

from src.db.connection import engine
from sqlalchemy import text

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("DEBUGGING EMPTY ALERT TABLES")
print("=" * 80)

# Step 1: Check database alert types
print("\n[STEP 1] DATABASE - Alert Types Distribution")
print("-" * 80)
try:
    results = engine.connect().execute(text("""
        SELECT alert_type, COUNT(*) as count, status
        FROM fact_alerts
        GROUP BY alert_type, status
        ORDER BY count DESC
    """)).fetchall()
    
    print("Alert types in database:")
    for r in results:
        print(f"  {r[0]} ({r[2]}): {r[1]} alerts")
        
    # Check for STUCK_IN_TRANSIT specifically
    stuck_count = engine.connect().execute(text("""
        SELECT COUNT(*) FROM fact_alerts 
        WHERE alert_type IN ('STUCK_IN_TRANSIT', 'DELAYED_TRANSIT')
        AND status = 'ACTIVE'
    """)).fetchone()[0]
    
    print(f"\nStuck inventory alerts (ACTIVE): {stuck_count}")
    
    # Check for LOW_YIELD
    yield_count = engine.connect().execute(text("""
        SELECT COUNT(*) FROM fact_alerts 
        WHERE alert_type = 'LOW_YIELD'
        AND status = 'ACTIVE'
    """)).fetchone()[0]
    
    print(f"Low yield alerts (ACTIVE): {yield_count}")
    
except Exception as e:
    print(f"❌ Database error: {e}")

# Step 2: Test API endpoints
print("\n[STEP 2] API ENDPOINTS TEST")
print("-" * 80)

print("\nTesting GET /api/v1/alerts/stuck-inventory")
try:
    response = requests.get(f"{BASE_URL}/api/v1/alerts/stuck-inventory", timeout=5)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {len(data)} alerts")
        
        if len(data) == 0:
            print("❌ API returns empty array!")
            print("   Checking SQL query in alerts.py...")
        else:
            print(f"✅ API returns {len(data)} alerts")
            print(f"Sample: {data[0]}")
    else:
        print(f"❌ Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Backend not running!")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTesting GET /api/v1/alerts/low-yield")
try:
    response = requests.get(f"{BASE_URL}/api/v1/alerts/low-yield", timeout=5)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {len(data)} alerts")
        
        if len(data) == 0:
            print("❌ API returns empty array!")
        else:
            print(f"✅ API returns {len(data)} alerts")
            print(f"Sample: {data[0]}")
    else:
        print(f"❌ Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Backend not running!")
except Exception as e:
    print(f"❌ Error: {e}")

# Step 3: Check exact SQL from alerts.py
print("\n[STEP 3] TESTING EXACT SQL FROM alerts.py")
print("-" * 80)

print("\nStuck inventory query:")
try:
    results = engine.connect().execute(text("""
        SELECT 
            id, 
            alert_type, 
            severity, 
            COALESCE(batch, entity_id) as title,
            'No message' as message,
            entity_type, 
            entity_id, 
            detected_at, 
            status
        FROM fact_alerts
        WHERE alert_type IN ('STUCK_IN_TRANSIT', 'DELAYED_TRANSIT')
          AND status = 'ACTIVE'
        ORDER BY severity DESC, detected_at DESC
        LIMIT 3
    """)).fetchall()
    
    print(f"Found {len(results)} results")
    for r in results:
        print(f"  ID {r[0]}: {r[1]} - {r[3]}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\nLow yield query:")
try:
    results = engine.connect().execute(text("""
        SELECT 
            id, 
            alert_type, 
            severity, 
            COALESCE(batch, entity_id) as title,
            'No message' as message,
            entity_type, 
            entity_id, 
            detected_at, 
            status
        FROM fact_alerts
        WHERE alert_type = 'LOW_YIELD'
          AND status = 'ACTIVE'
        ORDER BY severity DESC, detected_at DESC
        LIMIT 3
    """)).fetchall()
    
    print(f"Found {len(results)} results")
    for r in results:
        print(f"  ID {r[0]}: {r[1]} - {r[3]}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)
print("\n1. If DB has alerts but API returns 0 → Check alerts.py SQL query")
print("2. If DB query works but API fails → Check backend is running")
print("3. If API works but frontend empty → Check frontend API calls")
print("=" * 80)
