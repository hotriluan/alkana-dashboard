"""Quick validation of local database Phase 3 status"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

print("=" * 60)
print("LOCAL DATABASE - PHASE 3 STATUS")
print("=" * 60)

with engine.connect() as conn:
    # Check rows
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as rows, 
            COUNT(DISTINCT (material_code, plant_code, posting_date)) as unique
        FROM fact_inventory
    """))
    row = result.fetchone()
    
    print(f"\n📊 fact_inventory:")
    print(f"   Total rows: {row[0]:,}")
    print(f"   Unique combos: {row[1]:,}")
    print(f"   Duplicates: {row[0] - row[1]:,}")
    
    # Check constraint
    result = conn.execute(text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename='fact_inventory' 
        AND indexname='idx_fact_inventory_unique'
    """))
    idx = result.fetchone()
    
    print(f"\n🔒 UNIQUE Constraint:")
    print(f"   Status: {'✅ Active' if idx else '❌ Missing'}")
    
    # Check view
    result = conn.execute(text("SELECT COUNT(*) FROM view_inventory_current"))
    view_count = result.scalar()
    print(f"\n📈 view_inventory_current:")
    print(f"   Rows: {view_count:,}")

print("\n" + "=" * 60)
print("✅ LOCAL DATABASE READY" if row[0] == row[1] and idx else "⚠️ ISSUES DETECTED")
print("=" * 60)
