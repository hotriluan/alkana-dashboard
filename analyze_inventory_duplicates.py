"""
Phase 3 Step 1: Analyze Inventory Duplicates

Before making any changes, analyze the current state of fact_inventory
to understand the duplicate issue.

Skills: database, data-analysis, sequential-thinking
"""
import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    
    print("="*80)
    print("PHASE 3: INVENTORY DUPLICATION ANALYSIS")
    print("="*80)
    
    # Step 1: Total row count
    print("\n[1] Current State:")
    total_rows = db.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
    print(f"  Total rows in fact_inventory: {total_rows:,}")
    
    # Step 2: Unique combinations
    unique_combos = db.execute(text("""
        SELECT COUNT(DISTINCT (material_code, plant_code, posting_date))
        FROM fact_inventory
    """)).scalar()
    print(f"  Unique (material + plant + date): {unique_combos:,}")
    
    # Step 3: Duplicates
    duplicates = total_rows - unique_combos
    dup_pct = (duplicates / total_rows * 100) if total_rows > 0 else 0
    print(f"  Duplicate rows: {duplicates:,} ({dup_pct:.1f}%)")
    
    # Step 4: Examples of duplicates
    print("\n[2] Top 10 Duplicate Examples:")
    result = db.execute(text("""
        SELECT 
            material_code, 
            plant_code, 
            posting_date::text,
            COUNT(*) as duplicate_count,
            SUM(current_qty_kg) as total_kg
        FROM fact_inventory
        GROUP BY material_code, plant_code, posting_date
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)).fetchall()
    
    if result:
        for r in result:
            print(f"  Material: {r[0]}, Plant: {r[1]}, Date: {r[2]}")
            print(f"    Duplicates: {r[3]} rows, Total: {r[4]:.2f} kg")
    else:
        print("  ✅ No duplicates found!")
    
    # Step 5: Total inventory weight
    print("\n[3] Inventory Totals:")
    total_kg = db.execute(text("""
        SELECT SUM(qty_kg) FROM fact_inventory
    """)).scalar()
    print(f"  Current total: {total_kg:,.2f} kg")
    
    # What it should be (sum of unique records)
    correct_kg = db.execute(text("""
        SELECT SUM(total_kg) FROM (
            SELECT 
                material_code, 
                plant_code, 
                posting_date,
                SUM(qty_kg) as total_kg
            FROM fact_inventory
            GROUP BY material_code, plant_code, posting_date
        ) subq
    """)).scalar()
    print(f"  After deduplication: {correct_kg:,.2f} kg")
    
    inflation = total_kg - correct_kg if total_kg and correct_kg else 0
    inflation_pct = (inflation / correct_kg * 100) if correct_kg else 0
    print(f"  Inflation: {inflation:,.2f} kg ({inflation_pct:.1f}%)")
    
    # Step 6: Check view_inventory_current
    print("\n[4] View Analysis:")
    view_count = db.execute(text("SELECT COUNT(*) FROM view_inventory_current")).scalar()
    print(f"  Rows in view_inventory_current: {view_count:,}")
    
    view_total_kg = db.execute(text("""
        SELECT SUM(current_qty_kg) FROM view_inventory_current
    """)).scalar()
    print(f"  Total from view: {view_total_kg:,.2f} kg")
    
    # Summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    if dup_pct > 50:
        print(f"🔴 CRITICAL: {dup_pct:.1f}% of records are duplicates!")
        print(f"   - {duplicates:,} duplicate rows out of {total_rows:,}")
        print(f"   - Inflating inventory by {inflation:,.2f} kg ({inflation_pct:.1f}%)")
        print(f"\n✅ NEXT STEP: Run cleanup script to remove duplicates")
    elif dup_pct > 10:
        print(f"⚠️  WARNING: {dup_pct:.1f}% duplicates found")
    else:
        print(f"✅ Data quality good: Only {dup_pct:.1f}% duplicates")
    print("="*80)
    
    db.close()

if __name__ == "__main__":
    main()
