"""
Migration: Add snapshot_date column to raw_zrfi005 table

Run with:
    python scripts/migrate_add_ar_snapshot_date.py

Skills: database-operations
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from src.db.connection import engine

print("=" * 60)
print("MIGRATION: Add snapshot_date to raw_zrfi005")
print("=" * 60)

with engine.connect() as conn:
    # Check if column exists
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='raw_zrfi005' AND column_name='snapshot_date'
    """))
    
    if result.fetchone():
        print("✓ Column snapshot_date already exists")
    else:
        # Add snapshot_date column
        conn.execute(text("""
            ALTER TABLE raw_zrfi005 
            ADD COLUMN snapshot_date DATE
        """))
        conn.commit()
        print("✓ Added snapshot_date column to raw_zrfi005")

print()
print("=" * 60)
print("Migration completed successfully!")
print("=" * 60)
