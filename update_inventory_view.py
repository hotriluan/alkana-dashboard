"""
Phase 3 Step 4: Update view_inventory_current

Fix the GROUP BY clause to prevent creating duplicate rows
for materials with different UOMs or descriptions.

Skills: database, backend-development
"""
import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    
    print("="*80)
    print("PHASE 3: UPDATE VIEW_INVENTORY_CURRENT")
    print("="*80)
    
    # Step 1: Check current view row count
    print("\n[1] Before Fix:")
    count_before = db.execute(text("SELECT COUNT(*) FROM view_inventory_current")).scalar()
    total_kg_before = db.execute(text("SELECT SUM(current_qty_kg) FROM view_inventory_current")).scalar()
    print(f"  Rows: {count_before:,}")
    print(f"  Total kg: {total_kg_before:,.2f}")
    
    # Step 2: Drop and recreate view
    print("\n[2] Updating View Definition...")
    db.execute(text("DROP VIEW IF EXISTS view_inventory_current CASCADE"))
    db.execute(text("""
        CREATE VIEW view_inventory_current AS
        SELECT 
            fi.plant_code,
            fi.material_code,
            MAX(fi.material_description) as material_description,
            SUM(fi.qty) as current_qty,
            SUM(COALESCE(fi.qty_kg, 0)) as current_qty_kg,
            MAX(fi.uom) as uom,
            MAX(fi.posting_date) as last_movement
        FROM fact_inventory fi
        GROUP BY fi.plant_code, fi.material_code
        HAVING SUM(fi.qty) > 0
        ORDER BY fi.plant_code, fi.material_code
    """))
    db.commit()
    print("  ✓ View updated successfully")
    
    # Step 3: Check new view row count
    print("\n[3] After Fix:")
    count_after = db.execute(text("SELECT COUNT(*) FROM view_inventory_current")).scalar()
    total_kg_after = db.execute(text("SELECT SUM(current_qty_kg) FROM view_inventory_current")).scalar()
    print(f"  Rows: {count_after:,}")
    print(f"  Total kg: {total_kg_after:,.2f}")
    
    # Step 4: Show reduction
    print("\n[4] Impact:")
    row_reduction = count_before - count_after
    kg_reduction = total_kg_before - total_kg_after if total_kg_before and total_kg_after else 0
    
    print(f"  Row reduction: {row_reduction:,} rows ({row_reduction/count_before*100:.1f}%)")
    print(f"  Total kg change: {kg_reduction:,.2f} kg")
    
    if abs(kg_reduction) < 0.01:
        print("  ✅ Totals unchanged (good - no data loss)")
    else:
        print(f"  ⚠️  Total changed by {kg_reduction:,.2f} kg")
    
    # Summary
    print("\n" + "="*80)
    print("VIEW UPDATE SUMMARY")
    print("="*80)
    print("✅ view_inventory_current updated")
    print("   Changes:")
    print("     - GROUP BY: Only plant_code + material_code (removed description, uom)")
    print("     - Uses MAX() to pick one description/uom per material")
    print(f"     - Rows: {count_before:,} → {count_after:,}")
    print("\n📋 Remaining Tasks:")
    print("   - Update transform_mb51() to use UPSERT (ON CONFLICT)")
    print("="*80)
    
    db.close()

if __name__ == "__main__":
    main()
