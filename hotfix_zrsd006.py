#!/usr/bin/env python3
"""
Hotfix: Add missing row_hash column to raw_zrsd006 table
This column is required for upsert logic to detect duplicates
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
import os

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/alkana_dashboard")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check if column exists
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'raw_zrsd006' AND column_name = 'row_hash'
    """))
    
    if result.fetchone():
        print("✓ Column row_hash already exists in raw_zrsd006")
    else:
        print("🔄 Adding row_hash column to raw_zrsd006...")
        conn.execute(text("ALTER TABLE raw_zrsd006 ADD COLUMN row_hash VARCHAR(32)"))
        conn.commit()
        print("✓ Column added successfully")
        
        # Show table structure
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'raw_zrsd006'
            ORDER BY ordinal_position
        """))
        
        print("\nraw_zrsd006 table structure:")
        for col, dtype in result:
            print(f"  - {col}: {dtype}")

engine.dispose()
