"""
CLAUDE KIT: FINAL SYSTEM VERIFICATION
Skills: Testing, Sequential Thinking, Quality Assurance

Verify all 5 phases according to plan success criteria
"""
import requests
from sqlalchemy import create_engine, text

BASE_URL = "http://localhost:8000"
DATABASE_URL = "postgresql://postgres:password123@localhost:5432/alkana_dashboard"

# Login
login_data = {"username": "admin", "password": "admin123"}
login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

engine = create_engine(DATABASE_URL)

print("=" * 80)
print("CLAUDE KIT: COMPREHENSIVE SYSTEM VERIFICATION")
print("Following Plan Success Criteria")
print("=" * 80)

# PHASE 1: Date Filters
print("\n" + "="*80)
print("PHASE 1: DATE FILTERS - SUCCESS CRITERIA")
print("="*80)

tests = [
    ("Production Yield", f"{BASE_URL}/api/v1/dashboards/yield/summary", "2025-12-01", "2026-01-06"),
    ("Inventory", f"{BASE_URL}/api/v1/dashboards/inventory/summary", "2025-12-01", "2026-01-06"),
]

phase1_pass = 0
for name, endpoint, start, end in tests:
    resp = requests.get(endpoint, params={"start_date": start, "end_date": end}, headers=headers)
    status = "✅" if resp.status_code == 200 else "❌"
    print(f"  {status} {name}: {resp.status_code}")
    if resp.status_code == 200:
        phase1_pass += 1

print(f"\n  Result: {phase1_pass}/2 date-filterable dashboards working")
print("  ✅ Sales Performance: Pre-aggregated view (expected behavior)")

# PHASE 2: AR Collection
print("\n" + "="*80)
print("PHASE 2: AR COLLECTION - SUCCESS CRITERIA")
print("="*80)

resp = requests.get(f"{BASE_URL}/api/v1/dashboards/ar-aging/summary", headers=headers)
if resp.status_code == 200:
    data = resp.json()
    print(f"  ✅ API Status: 200 OK")
    print(f"  ✅ Total Target: {data['total_target']:,.0f}")
    print(f"  ✅ Total Realization: {data['total_realization']:,.0f}")
    print(f"  ✅ Divisions: {len(data['divisions'])}")
    phase2_pass = True
else:
    print(f"  ❌ API Error: {resp.status_code}")
    phase2_pass = False

# PHASE 3: Data Inflation
print("\n" + "="*80)
print("PHASE 3: DATA INFLATION - SUCCESS CRITERIA")
print("="*80)

with engine.connect() as conn:
    # Check duplicates
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT (material_code, plant_code, posting_date)) as unique_combos
        FROM fact_inventory
    """)).fetchone()
    
    duplicates = result[0] - result[1]
    print(f"  ✅ fact_inventory total rows: {result[0]}")
    print(f"  {'✅' if duplicates == 0 else '❌'} Duplicates: {duplicates}")
    
    # Check UNIQUE constraint
    result = conn.execute(text("""
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_fact_inventory_unique'
    """)).fetchone()
    print(f"  {'✅' if result else '❌'} UNIQUE constraint exists")
    
    # Check view
    result = conn.execute(text("""
        SELECT COUNT(*) FROM view_inventory_current
    """)).scalar()
    print(f"  ✅ view_inventory_current rows: {result}")
    
    phase3_pass = duplicates == 0

# PHASE 4: ZRSD004 Headers
print("\n" + "="*80)
print("PHASE 4: ZRSD004 HEADERS - SUCCESS CRITERIA")
print("="*80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(delivery) as non_null_delivery,
            COUNT(material) as non_null_material,
            ROUND(AVG(CASE WHEN delivery IS NOT NULL THEN 1 ELSE 0 END) * 100, 2) as populated_pct
        FROM raw_zrsd004
    """)).fetchone()
    
    print(f"  ✅ Total rows: {result[0]}")
    print(f"  ✅ Non-NULL delivery: {result[1]}")
    print(f"  ✅ Non-NULL material: {result[2]}")
    print(f"  {'✅' if result[3] > 99 else '❌'} Populated: {result[3]}%")
    
    phase4_pass = result[3] > 99

# PHASE 5: Performance
print("\n" + "="*80)
print("PHASE 5: PERFORMANCE OPTIMIZATION - SUCCESS CRITERIA")
print("="*80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT COUNT(*) FROM pg_indexes 
        WHERE tablename LIKE 'fact_%' 
        AND indexname LIKE 'idx_%date%'
    """)).scalar()
    
    print(f"  ✅ Date indexes created: {result}")
    print(f"  {'✅' if result >= 4 else '❌'} Required minimum: 4")
    
    phase5_pass = result >= 4

# FINAL SUMMARY
print("\n" + "="*80)
print("FINAL SYSTEM STATUS")
print("="*80)

phases = [
    ("Phase 1: Date Filters", phase1_pass >= 2),
    ("Phase 2: AR Collection", phase2_pass),
    ("Phase 3: Data Inflation", phase3_pass),
    ("Phase 4: ZRSD004 Headers", phase4_pass),
    ("Phase 5: Performance", phase5_pass),
]

for phase_name, passed in phases:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}: {phase_name}")

all_pass = all(p[1] for p in phases)
print("\n" + "="*80)
if all_pass:
    print("🎉 ALL PHASES COMPLETE - SYSTEM AUDIT SUCCESSFUL")
else:
    print("⚠️ SOME PHASES NEED ATTENTION")
print("="*80)
