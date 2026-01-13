#!/usr/bin/env python3
"""
Hotfix: Add missing row_hash column to raw_zrsd006 via backend DB session
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # Check if column exists
    result = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'raw_zrsd006' AND column_name = 'row_hash'
    """)).fetchone()
    
    if result:
        print("✓ Column row_hash already exists")
    else:
        print("🔄 Adding row_hash column to raw_zrsd006...")
        db.execute(text("ALTER TABLE raw_zrsd006 ADD COLUMN row_hash VARCHAR(32)"))
        db.commit()
        print("✓ Column added successfully")
        
        # Show table columns
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'raw_zrsd006'
            ORDER BY ordinal_position DESC
            LIMIT 5
        """)).fetchall()
        
        print("\nLast 5 columns in raw_zrsd006:")
        for col, dtype in result:
            print(f"  - {col}: {dtype}")

except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
