"""
Clean inventory duplicates - OPTIMIZED bulk version
Keeps MIN(id) for each (material_code, plant_code, posting_date)
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use environment variable from Docker container or local .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found!")
    exit(1)

engine = create_engine(DATABASE_URL)  # Removed AUTOCOMMIT for transaction safety

print("🧹 Cleaning fact_inventory duplicates (BULK)...")
print()

try:
    with engine.begin() as conn:  # Explicit transaction block
        # Check before
        before = conn.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
        print(f"Before: {before:,} rows")
        
        # Check duplicates
        result = conn.execute(text("""
            SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code, posting_date)) as dupes
            FROM fact_inventory
        """))
        dupes = result.scalar()
        print(f"Duplicates: {dupes:,} rows")
        print()
        
        if dupes == 0:
            print("✅ No duplicates to clean!")
            exit(0)
        
        print(f"Deleting {dupes:,} duplicate rows (keeping MIN(id) for each combination)...")
        print()
        
        # BULK DELETE using JOIN - much faster and safer
        print("Executing bulk delete with transaction safety...")
        conn.execute(text("""
            DELETE FROM fact_inventory f
            USING (
                SELECT material_code, plant_code, posting_date, MIN(id) as keep_id
                FROM fact_inventory
                GROUP BY material_code, plant_code, posting_date
            ) keepers
            WHERE f.material_code = keepers.material_code
              AND f.plant_code = keepers.plant_code
              AND f.posting_date = keepers.posting_date
              AND f.id != keepers.keep_id
        """))
        
        # Check after
        after = conn.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
        removed = before - after
        
        print(f"After: {after:,} rows")
        print(f"Removed: {removed:,} duplicates")
        print()
        
        # Verify
        result = conn.execute(text("""
            SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code, posting_date)) as remaining
            FROM fact_inventory
        """))
        remaining = result.scalar()
        
        if remaining == 0:
            print("✅ All duplicates removed!")
            print("✅ Each (material_code, plant_code, posting_date) has exactly 1 row")
            print("✅ Transaction committed successfully")
        else:
            print(f"⚠️ Still {remaining:,} duplicates remaining")
            conn.rollback()
            raise Exception(f"Cleanup incomplete: {remaining} duplicates remain")

except Exception as e:
    print(f"\n❌ Error during cleanup: {e}")
    print("Transaction rolled back - no changes made to database")
    import traceback
    traceback.print_exc()
    exit(1)
