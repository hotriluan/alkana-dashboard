"""
Migration: Add row_hash column to raw_zrfi005

Run with:
    python scripts/migrate_add_row_hash_zrfi005.py

Skills: database-operations
"""
import sys
sys.path.insert(0, '.')

from src.db.connection import engine
from sqlalchemy import text

print("=" * 70)
print("MIGRATION: Add row_hash column to raw_zrfi005")
print("=" * 70)

# Add row_hash column using raw SQL
with engine.connect() as conn:
    try:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='raw_zrfi005' AND column_name='row_hash'
        """))
        
        if result.fetchone():
            print("✓ row_hash column already exists")
        else:
            # Add column
            conn.execute(text("""
                ALTER TABLE raw_zrfi005 
                ADD COLUMN row_hash VARCHAR(64)
            """))
            conn.commit()
            print("✓ row_hash column added to raw_zrfi005")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise

print()
print("=" * 70)
print("Migration completed successfully!")
print("=" * 70)
