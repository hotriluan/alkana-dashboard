"""
Phase 3 Data Inflation Fix: Add UNIQUE Constraint to fact_inventory
Created: 2026-02-09
Purpose: Prevent duplicate inventory records for the same material/plant/date combination

Background:
- Cleaned 1,220,327 duplicate rows (1.66M → 82,883 unique rows)
- Each (material_code, plant_code, posting_date) should have exactly 1 row
- UNIQUE constraint prevents future duplicates from ETL transforms

Expected Impact:
- Prevents data inflation in inventory totals
- Enforces data integrity at database level
- ETL transforms will fail-fast on duplicate insertions instead of silently creating bad data
"""

from sqlalchemy import create_engine, text
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_unique_constraint(database_url: str, dry_run: bool = False):
    """
    Add UNIQUE constraint to fact_inventory
    
    Args:
        database_url: PostgreSQL connection string
        dry_run: If True, only print SQL without executing
    """
    engine = create_engine(database_url)
    
    constraint_sql = """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_inventory_unique
        ON fact_inventory (material_code, plant_code, posting_date)
    """
    
    print("=" * 80)
    print("PHASE 3: ADD UNIQUE CONSTRAINT TO fact_inventory")
    print("=" * 80)
    print()
    
    if dry_run:
        print("🔍 DRY RUN MODE - SQL will be printed but not executed")
        print()
    
    print("📋 Constraint Details:")
    print("  Table: fact_inventory")
    print("  Columns: (material_code, plant_code, posting_date)")
    print("  Type: UNIQUE INDEX")
    print("  Name: idx_fact_inventory_unique")
    print()
    
    print("✓ Purpose:")
    print("  - Prevent duplicate inventory snapshots for same material/plant/date")
    print("  - Enforce data integrity at database level")
    print("  - Fail-fast on ETL transform errors")
    print()
    
    if dry_run:
        print("SQL to be executed:")
        print(constraint_sql)
        return
    
    try:
        with engine.connect() as conn:
            print("🔧 Checking for existing duplicates...")
            
            # Verify no duplicates remain
            result = conn.execute(text("""
                SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code, posting_date)) as dupes
                FROM fact_inventory
            """))
            dupes = result.scalar()
            
            if dupes > 0:
                print(f"❌ ERROR: Found {dupes:,} duplicate rows!")
                print("   Run clean_inventory_duplicates_bulk.py first to remove duplicates")
                return False
            
            print(f"✓ No duplicates found - safe to add constraint")
            print()
            
            print("🔧 Creating UNIQUE index...")
            conn.execute(text(constraint_sql))
            conn.commit()
            
            print("✓ UNIQUE constraint added successfully!")
            print()
            
            # Verify constraint exists
            result = conn.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'fact_inventory'
                AND indexname = 'idx_fact_inventory_unique'
            """))
            index = result.fetchone()
            
            if index:
                print("✓ Verification: Constraint is active")
                print(f"  Index: {index[0]}")
                print(f"  Definition: {index[1]}")
            else:
                print("⚠️  Warning: Could not verify constraint creation")
            
            print()
            print("=" * 80)
            print("✓ PHASE 3 CONSTRAINT COMPLETE")
            print("=" * 80)
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment!")
        print("Set DATABASE_URL or run inside Docker container")
        sys.exit(1)
    
    # Check for --dry-run flag
    dry_run = '--dry-run' in sys.argv
    
    success = add_unique_constraint(database_url, dry_run)
    sys.exit(0 if success else 1)
