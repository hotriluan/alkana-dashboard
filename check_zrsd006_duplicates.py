#!/usr/bin/env python3
"""Check for duplicates in raw_zrsd006 table after multiple uploads"""

from pathlib import Path
from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = "postgresql://postgres:password@localhost:5432/alkana_dashboard"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check total record count
    result = conn.execute(text("SELECT COUNT(*) FROM raw_zrsd006"))
    total_count = result.scalar()
    print(f"Total records in raw_zrsd006: {total_count}")
    
    # Check for duplicates by business key (material + dist_channel)
    result = conn.execute(text("""
        SELECT material, dist_channel, COUNT(*) as count
        FROM raw_zrsd006
        GROUP BY material, dist_channel
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 20
    """))
    
    duplicates = result.fetchall()
    if duplicates:
        print(f"\n⚠️  Found {len(duplicates)} business keys with duplicates:")
        for material, dist_channel, count in duplicates:
            print(f"  - Material: {material}, Channel: {dist_channel} → {count} records")
    else:
        print("\n✓ No duplicates found by business key (material + dist_channel)")
    
    # Check unique materials and channels
    result = conn.execute(text("SELECT COUNT(DISTINCT material) FROM raw_zrsd006"))
    unique_materials = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(DISTINCT dist_channel) FROM raw_zrsd006"))
    unique_channels = result.scalar()
    
    print(f"\n📊 Statistics:")
    print(f"  - Unique materials: {unique_materials}")
    print(f"  - Unique distribution channels: {unique_channels}")
    
    # Check row_hash uniqueness (should all be unique if no duplicates)
    result = conn.execute(text("""
        SELECT COUNT(*) as total, COUNT(DISTINCT row_hash) as unique_hashes
        FROM raw_zrsd006
    """))
    total, unique = result.fetchone()
    print(f"  - Total rows: {total}, Unique hashes: {unique}")
    
    if total == unique:
        print("  ✓ All rows have unique row_hash (no exact duplicates)")
    else:
        print(f"  ⚠️  {total - unique} rows have duplicate row_hash!")
        
        # Show which row_hash values appear multiple times
        result = conn.execute(text("""
            SELECT row_hash, COUNT(*) as count
            FROM raw_zrsd006
            GROUP BY row_hash
            HAVING COUNT(*) > 1
            LIMIT 10
        """))
        
        dup_hashes = result.fetchall()
        print(f"\n  Duplicate row_hash values:")
        for row_hash, count in dup_hashes:
            print(f"    - {row_hash}: {count} records")
