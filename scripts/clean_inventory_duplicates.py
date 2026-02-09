"""
Clean existing inventory duplicates before adding constraints
Part of Phase 3: Data Inflation Fix
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment!")
    print("Please set DATABASE_URL in .env file")
    exit(1)

engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("🧹 Cleaning fact_inventory duplicates...")
print()

with engine.connect() as conn:
    # Check before
    before = conn.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
    print(f"Before: {before:,} rows")
    
    # Get duplicates - one row per (material, plant, date)
    result = conn.execute(text("""
        SELECT material_code, plant_code, posting_date, COUNT(*) as cnt
        FROM fact_inventory
        GROUP BY material_code, plant_code, posting_date
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()
    print(f"Found {len(duplicates)} duplicate combinations")
    print()
    
    if len(duplicates) == 0:
        print("✅ No duplicates to clean!")
        exit(0)
    
    print(f"Cleaning {len(duplicates)} duplicate groups...")
    
    # Delete duplicates keeping MIN(id)
    for i, (material_code, plant_code, posting_date, count) in enumerate(duplicates, 1):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(duplicates)} groups cleaned...")
        
        conn.execute(text("""
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
        """), {'mat': material_code, 'plant': plant_code, 'date': posting_date})
    
    print(f"  Progress: {len(duplicates)}/{len(duplicates)} groups cleaned...")
    print()
    
    # Check after
    after = conn.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
    print(f"After: {after:,} rows")
    print(f"Removed: {before - after:,} duplicates")
    print()
    
    # Verify no duplicates remain
    result = conn.execute(text("""
        SELECT material_code, plant_code, posting_date, COUNT(*) as cnt
        FROM fact_inventory
        GROUP BY material_code, plant_code, posting_date
        HAVING COUNT(*) > 1
    """))
    remaining_duplicates = result.fetchall()
    
    if len(remaining_duplicates) == 0:
        print("✅ All duplicates removed!")
        print("✅ Each (material_code, plant_code, posting_date) now has exactly 1 row")
    else:
        print(f"⚠️ Still {len(remaining_duplicates)} duplicate groups remaining")
        print("First 10 remaining duplicates:")
        for mat, plant, date, cnt in remaining_duplicates[:10]:
            print(f"  {mat} @ {plant} on {date}: {cnt} rows")
