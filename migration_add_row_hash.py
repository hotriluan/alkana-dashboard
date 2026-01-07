"""
Database migration: Add row_hash column to all raw tables

This enables:
1. Change detection (skip unchanged rows on re-upload)
2. Duplicate detection
3. Data lineage tracking
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

raw_tables = [
    'raw_cooispi',
    'raw_mb51',
    'raw_zrmm024',
    'raw_zrsd002',
    'raw_zrsd004',
    'raw_zrsd006',
    'raw_zrfi005',
    'raw_target'
]

print("="*80)
print("  ADDING row_hash COLUMN TO RAW TABLES")
print("="*80)

with engine.connect() as conn:
    for table in raw_tables:
        try:
            # Check if column exists
            check_sql = text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name=:table AND column_name='row_hash'
            """)
            exists = conn.execute(check_sql, {'table': table}).fetchone()
            
            if exists:
                print(f"✓ {table}: row_hash already exists")
                continue
            
            # Add column
            sql = text(f"""
                ALTER TABLE {table}
                ADD COLUMN row_hash VARCHAR(32)
            """)
            conn.execute(sql)
            conn.commit()
            
            print(f"✓ {table}: Added row_hash column")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ {table}: {e}")

print("\n✅ Migration completed!")
print("Now loaders can track changes and detect duplicates")
