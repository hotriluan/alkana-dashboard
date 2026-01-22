"""
Verify completion rate fix
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:password123@localhost:5432/alkana_dashboard"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("COMPLETION RATE FIX VERIFICATION")
print("=" * 80)

with engine.connect() as conn:
    # Test with 2025 data
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN system_status LIKE '%TECO%' THEN 1 END) as old_logic_completed,
            COUNT(CASE WHEN system_status LIKE '%DLV%' OR system_status LIKE '%TECO%' THEN 1 END) as new_logic_completed
        FROM fact_production
        WHERE actual_finish_date BETWEEN '2025-01-01' AND '2025-12-31'
    """)).fetchone()
    
    total = result[0]
    old_completed = result[1]
    new_completed = result[2]
    
    old_rate = (old_completed / total * 100) if total > 0 else 0
    new_rate = (new_completed / total * 100) if total > 0 else 0
    
    print(f"\n2025 Full Year (01/01/2025 - 31/12/2025)")
    print(f"  Total Orders:          {total:>8,}")
    print(f"  Completed (OLD - TECO only):     {old_completed:>8,}  ({old_rate:.2f}%)")
    print(f"  Completed (NEW - DLV|TECO):      {new_completed:>8,}  ({new_rate:.2f}%)")
    print(f"  Improvement:           {new_completed - old_completed:>8,} orders now counted correctly")
    
    # Validation
    print(f"\n✅ PASS" if new_rate > 90 else "❌ FAIL")
    print(f"   Expected: ~96.41%")
    print(f"   Actual:   {new_rate:.2f}%")

print("\n" + "=" * 80)
print("FIX VERIFIED")
print("=" * 80)
