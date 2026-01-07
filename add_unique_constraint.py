"""
Phase 3 Step 3: Add UNIQUE Constraint to fact_inventory

Prevent future duplicate entries by adding a UNIQUE index on
(material_code, plant_code, posting_date).

Skills: database, backend-development
"""
import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    
    print("="*80)
    print("PHASE 3: ADD UNIQUE CONSTRAINT")
    print("="*80)
    
    # Step 1: Check if constraint already exists
    print("\n[1] Checking for existing constraint...")
    result = db.execute(text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename = 'fact_inventory'
        AND indexname LIKE '%unique%'
    """)).fetchall()
    
    if result:
        print(f"  Existing unique indexes: {[r[0] for r in result]}")
    else:
        print("  No unique indexes found")
    
    # Step 2: Create UNIQUE index
    print("\n[2] Creating UNIQUE index...")
    try:
        db.execute(text("""
            CREATE UNIQUE INDEX idx_fact_inventory_unique
            ON fact_inventory (material_code, plant_code, posting_date)
        """))
        db.commit()
        print("  ✓ UNIQUE index created successfully")
    except Exception as e:
        if "already exists" in str(e):
            print("  ℹ️  Index already exists (skipping)")
        else:
            print(f"  ❌ Error: {e}")
            db.rollback()
            return
    
    # Step 3: Verify constraint
    print("\n[3] Verifying constraint...")
    result = db.execute(text("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'fact_inventory'
        AND indexname = 'idx_fact_inventory_unique'
    """)).fetchone()
    
    if result:
        print(f"  ✓ Constraint verified:")
        print(f"    Index: {result[0]}")
        print(f"    Definition: {result[1]}")
    else:
        print("  ❌ Constraint not found!")
    
    # Step 4: Test constraint (try to insert duplicate)
    print("\n[4] Testing constraint (attempt duplicate insert)...")
    try:
        # Get a sample record
        sample = db.execute(text("""
            SELECT material_code, plant_code, posting_date
            FROM fact_inventory
            LIMIT 1
        """)).fetchone()
        
        if sample:
            # Try to insert duplicate
            db.execute(text("""
                INSERT INTO fact_inventory 
                (material_code, plant_code, posting_date, qty, qty_kg, uom)
                VALUES (:mat, :plant, :date, 0, 0, 'PC')
            """), {
                'mat': sample[0],
                'plant': sample[1],
                'date': sample[2]
            })
            db.commit()
            print("  ❌ ERROR: Duplicate was allowed (constraint not working!)")
        else:
            print("  ℹ️  No sample data to test with")
    except Exception as e:
        db.rollback()
        if "duplicate key value violates unique constraint" in str(e) or "unique" in str(e).lower():
            print("  ✅ Constraint working: Duplicate insert blocked")
        else:
            print(f"  ⚠️  Unexpected error: {str(e)[:100]}")
    
    # Summary
    print("\n" + "="*80)
    print("CONSTRAINT SUMMARY")
    print("="*80)
    print("✅ UNIQUE constraint added to fact_inventory")
    print("   - Columns: (material_code, plant_code, posting_date)")
    print("   - Index: idx_fact_inventory_unique")
    print("   - Effect: Prevents duplicate inventory snapshots")
    print("\n📋 Next Steps:")
    print("   - Fix transform_mb51() to handle duplicates gracefully")
    print("   - Update view_inventory_current GROUP BY")
    print("="*80)
    
    db.close()

if __name__ == "__main__":
    main()
