"""
Fix duplicates - Simple version with explicit commits
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Use autocommit mode
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("="*80)
print("  FIX REMAINING DUPLICATES")
print("="*80)

with engine.connect() as conn:
    
    # Fix 1: fact_p02_p01_yield
    print("\n[1/3] fact_p02_p01_yield...")
    before = conn.execute(text("SELECT COUNT(*) FROM fact_p02_p01_yield")).scalar()
    print(f"  Before: {before:,}")
    
    conn.execute(text("""
        DELETE FROM fact_p02_p01_yield
        WHERE id NOT IN (
            SELECT MIN(id) FROM fact_p02_p01_yield
            GROUP BY p02_batch, p01_batch
        )
    """))
    
    after = conn.execute(text("SELECT COUNT(*) FROM fact_p02_p01_yield")).scalar()
    print(f"  After: {after:,}")
    print(f"  Removed: {before - after:,} ✅")
    
    # Fix 2: fact_target
    print("\n[2/3] fact_target...")
    before = conn.execute(text("SELECT COUNT(*) FROM fact_target")).scalar()
    print(f"  Before: {before:,}")
    
    conn.execute(text("""
        DELETE FROM fact_target
        WHERE id NOT IN (
            SELECT MIN(id) FROM fact_target
            GROUP BY salesman_name, semester, year
        )
    """))
    
    after = conn.execute(text("SELECT COUNT(*) FROM fact_target")).scalar()
    print(f"  After: {after:,}")
    print(f"  Removed: {before - after:,} ✅")
    
    # Fix 3: raw_mb51
    print("\n[3/3] raw_mb51...")
    before = conn.execute(text("SELECT COUNT(*) FROM raw_mb51")).scalar()
    print(f"  Before: {before:,}")
    
    conn.execute(text("""
        DELETE FROM raw_mb51
        WHERE id NOT IN (
            SELECT MIN(id) FROM raw_mb51
            GROUP BY row_hash
        )
    """))
    
    after = conn.execute(text("SELECT COUNT(*) FROM raw_mb51")).scalar()
    print(f"  After: {after:,}")
    print(f"  Removed: {before - after:,} ✅")
    
    print("\n" + "="*80)
    print("  ALL DUPLICATES REMOVED")
    print("="*80)
