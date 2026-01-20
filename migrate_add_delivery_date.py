#!/usr/bin/env python3
"""
Database Migration: Add delivery_date column to fact_delivery table
"""
from src.db.connection import engine
from sqlalchemy import text

def migrate_add_delivery_date():
    """Add delivery_date column to fact_delivery if it doesn't exist"""
    with engine.connect() as conn:
        try:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'fact_delivery'
                    AND column_name = 'delivery_date'
                )
            """))
            column_exists = result.scalar()
            
            if column_exists:
                print("✓ Column delivery_date already exists in fact_delivery")
                return
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE fact_delivery
                ADD COLUMN delivery_date DATE
            """))
            conn.commit()
            print("✓ Successfully added delivery_date column to fact_delivery")
            
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            conn.rollback()
            raise

if __name__ == '__main__':
    print("=" * 70)
    print("Database Migration: Add delivery_date column")
    print("=" * 70)
    migrate_add_delivery_date()
    print("=" * 70)
    print("Migration completed!")
