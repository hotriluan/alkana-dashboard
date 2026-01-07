"""
Phase 3 Step 2: Clean Inventory Duplicates

Remove duplicate rows from fact_inventory, keeping only one record
per (material_code, plant_code, posting_date) combination.

Skills: database, backend-development, data-cleanup
"""
import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    
    print("="*80)
    print("PHASE 3: CLEAN INVENTORY DUPLICATES")
    print("="*80)
    
    # Step 1: Check before
    print("\n[1] Before Cleanup:")
    total_before = db.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
    print(f"  Total rows: {total_before:,}")
    
    unique_combos = db.execute(text("""
        SELECT COUNT(DISTINCT (material_code, plant_code, posting_date))
        FROM fact_inventory
    """)).scalar()
    print(f"  Unique combinations: {unique_combos:,}")
    duplicates_before = total_before - unique_combos
    print(f"  Duplicates to remove: {duplicates_before:,}")
    
    # Step 2: Get list of duplicate combinations
    print("\n[2] Finding Duplicates...")
    result = db.execute(text("""
        SELECT material_code, plant_code, posting_date
        FROM fact_inventory
        GROUP BY material_code, plant_code, posting_date
        HAVING COUNT(*) > 1
    """)).fetchall()
    
    print(f"  Found {len(result):,} duplicate combinations")
    
    # Step 3: Delete duplicates (keep MIN(id))
    print("\n[3] Removing Duplicates...")
    deleted_count = 0
    
    for i, (material_code, plant_code, posting_date) in enumerate(result):
        if i % 100 == 0 and i > 0:
            print(f"  Progress: {i}/{len(result)} combinations processed...")
        
        # Delete all except the one with minimum ID
        result_del = db.execute(text("""
            DELETE FROM fact_inventory
            WHERE material_code = :mat
            AND plant_code = :plant
            AND posting_date = :date
            AND id NOT IN (
                SELECT MIN(id)
                FROM fact_inventory
                WHERE material_code = :mat
                AND plant_code = :plant
                AND posting_date = :date
            )
        """), {
            'mat': material_code,
            'plant': plant_code,
            'date': posting_date
        })
        deleted_count += result_del.rowcount
    
    # Commit changes
    db.commit()
    print(f"  ✓ Deleted {deleted_count:,} duplicate rows")
    
    # Step 4: Verify
    print("\n[4] After Cleanup:")
    total_after = db.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
    print(f"  Total rows: {total_after:,}")
    
    remaining_dups = db.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code, posting_date))
        FROM fact_inventory
    """)).scalar()
    print(f"  Remaining duplicates: {remaining_dups}")
    
    # Summary
    print("\n" + "="*80)
    print("CLEANUP SUMMARY")
    print("="*80)
    print(f"  Before: {total_before:,} rows")
    print(f"  After: {total_after:,} rows")
    print(f"  Removed: {total_before - total_after:,} duplicates")
    
    if remaining_dups == 0:
        print("\n✅ SUCCESS: All duplicates removed!")
        print("   Next step: Add UNIQUE constraint to prevent future duplicates")
    else:
        print(f"\n⚠️  WARNING: {remaining_dups} duplicates still remain")
    print("="*80)
    
    db.close()

if __name__ == "__main__":
    main()
