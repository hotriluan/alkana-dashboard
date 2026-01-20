#!/usr/bin/env python3
"""
Fix OTIF delivery_date population issue

Problem: existing fact_delivery records have delivery_date = NULL
Root Cause: row_hash check skips updates when only delivery_date changed
Solution: Force update delivery_date from raw_zrsd004 to fact_delivery

ClaudeKit Compliance: KISS principle - direct SQL update
"""
from src.db.connection import SessionLocal
from sqlalchemy import text

def fix_delivery_dates():
    print("=" * 70)
    print("OTIF Fix: Populate delivery_date in fact_delivery")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Count records needing update
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM fact_delivery fd
            WHERE fd.delivery_date IS NULL
            AND EXISTS (
                SELECT 1 FROM raw_zrsd004 r 
                WHERE r.delivery = fd.delivery 
                AND r.line_item = fd.line_item
                AND r.delivery_date IS NOT NULL
            )
        """))
        count_before = result.scalar()
        print(f"📊 Records needing update: {count_before}")
        
        if count_before == 0:
            print("✓ All records already have delivery_date - no update needed")
            db.close()
            return
        
        # Update fact_delivery.delivery_date from raw_zrsd004
        update_sql = text("""
            UPDATE fact_delivery fd
            SET delivery_date = r.delivery_date::date
            FROM raw_zrsd004 r
            WHERE r.delivery = fd.delivery 
            AND r.line_item = fd.line_item
            AND fd.delivery_date IS NULL
            AND r.delivery_date IS NOT NULL
        """)
        
        result = db.execute(update_sql)
        db.commit()
        
        updated = result.rowcount
        print(f"✓ Updated {updated} records with delivery_date")
        
        # Verify specific delivery
        verify = db.execute(text("""
            SELECT delivery, delivery_date, actual_gi_date
            FROM fact_delivery
            WHERE delivery = '1910053734'
            LIMIT 5
        """))
        
        print("\n📋 Verification (Delivery 1910053734):")
        for row in verify:
            print(f"  Delivery: {row[0]}, Planned: {row[1]}, Actual: {row[2]}")
        
        db.close()
        
    except Exception as e:
        print(f"✗ Update failed: {e}")
        db.rollback()
        db.close()
        raise
    
    print("=" * 70)
    print("Fix completed successfully!")
    print("=" * 70)

if __name__ == '__main__':
    fix_delivery_dates()
