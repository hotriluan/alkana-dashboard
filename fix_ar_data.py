"""
CLAUDE KIT: Database + Sequential Thinking
Fix AR data: Populate snapshot_date in raw, then re-transform
"""
from sqlalchemy import create_engine, text
from datetime import date

DATABASE_URL = "postgresql://postgres:password123@localhost:5432/alkana_dashboard"
engine = create_engine(DATABASE_URL)

print("=" * 70)
print("CLAUDE KIT: FIX AR DATA PIPELINE")
print("Skills: Database, Sequential Thinking, Backend Development")
print("=" * 70)

with engine.begin() as conn:
    # Step 1: Check current state
    print("\n[STEP 1] Check current state")
    result = conn.execute(text("SELECT COUNT(*) FROM raw_zrfi005")).scalar()
    print(f"  raw_zrfi005: {result} rows")
    
    result = conn.execute(text("SELECT COUNT(*) FROM fact_ar_aging")).scalar()
    print(f"  fact_ar_aging: {result} rows")
    
    # Step 2: Populate snapshot_date in raw_zrfi005
    print("\n[STEP 2] Populate snapshot_date in raw_zrfi005")
    print("  Setting all raw records to snapshot_date = 2026-01-06")
    
    result = conn.execute(text("""
        UPDATE raw_zrfi005 
        SET snapshot_date = :snap_date 
        WHERE snapshot_date IS NULL
    """), {"snap_date": date(2026, 1, 6)})
    
    print(f"  ✅ Updated {result.rowcount} rows")
    
    # Step 3: Verify update
    print("\n[STEP 3] Verify update")
    result = conn.execute(text("""
        SELECT snapshot_date, COUNT(*) 
        FROM raw_zrfi005 
        GROUP BY snapshot_date
    """)).fetchall()
    
    for row in result:
        print(f"  {row[0]}: {row[1]} rows")

print("\n[STEP 4] Re-run transform to populate fact_ar_aging")
print("  Running transformer...")

# Import and run transform
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from db.database import get_db
from etl.transform import DataTransformer

db = next(get_db())
transformer = DataTransformer(db)

# Transform AR data
transformer.transform_ar_aging()
db.close()

# Step 5: Verify final state
print("\n[STEP 5] Verify final state")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            snapshot_date,
            COUNT(*) as rows,
            SUM(total_target) as target,
            SUM(total_realization) as realization
        FROM fact_ar_aging
        GROUP BY snapshot_date
    """)).fetchall()
    
    for row in result:
        print(f"  {row[0]}: {row[1]} rows, Target: {row[2]:,.0f}, Realization: {row[3]:,.0f}")

print("\n" + "=" * 70)
print("✅ FIX COMPLETE - AR data restored")
print("=" * 70)
