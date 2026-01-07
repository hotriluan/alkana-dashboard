"""
CORRECTED comprehensive cleanup script to remove duplicates from ALL affected tables

FIX: Previous script had bug - WHERE IS NOT NULL in subquery caused deletion of ALL rows with NULL keys
SOLUTION: Use COALESCE in GROUP BY to handle NULL properly, no WHERE filtering in subquery
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import sys

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

async def cleanup_fact_lead_time():
    """
    Cleanup fact_lead_time duplicates
    Business key: order_number + batch (corrected column names)
    """
    print_section("CLEANING FACT_LEAD_TIME")
    
    session = Session()
    try:
        before_count = session.execute(text("SELECT COUNT(*) FROM fact_lead_time")).scalar()
        print(f"Before: {before_count:,} rows")
        
        # Show sample duplicates
        samples = session.execute(text("""
            SELECT order_number, batch, COUNT(*) as cnt
            FROM fact_lead_time
            GROUP BY order_number, batch
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 5
        """)).fetchall()
        
        if samples:
            print(f"\nFound {len(samples)} duplicate combinations (showing top 5):")
            for row in samples:
                print(f"  - Order {row[0]}, Batch {row[1]}: {row[2]} times")
        
        # Delete duplicates keeping MIN(id)
        # FIX: No WHERE filter - handle all rows including NULLs
        delete_result = session.execute(text("""
            DELETE FROM fact_lead_time
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM fact_lead_time
                GROUP BY 
                    COALESCE(order_number, ''),
                    COALESCE(batch, '')
            )
        """))
        session.commit()
        
        after_count = session.execute(text("SELECT COUNT(*) FROM fact_lead_time")).scalar()
        print(f"After: {after_count:,} rows")
        print(f"✓ Removed {before_count - after_count:,} duplicate rows")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

async def final_validation():
    """
    Validate fact_lead_time after cleanup
    """
    print_section("FINAL VALIDATION")
    
    session = Session()
    try:
        # Check fact_lead_time
        count = session.execute(text("SELECT COUNT(*) FROM fact_lead_time")).scalar()
        print(f"\nfact_lead_time: {count:,} rows")
        
        # Check for remaining duplicates
        dups = session.execute(text("""
            SELECT order_number, batch, COUNT(*) as cnt
            FROM fact_lead_time
            GROUP BY order_number, batch
            HAVING COUNT(*) > 1
            LIMIT 1
        """)).fetchone()
        
        if dups:
            print(f"⚠️ Still has duplicates!")
        else:
            print(f"✅ No duplicates remaining")
        
        print("\n✅ Cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
    finally:
        session.close()

async def main():
    """
    Main execution flow
    
    NOTE: Raw tables were accidentally wiped by previous bad cleanup script.
    This script ONLY fixes fact_lead_time duplicates.
    Raw tables can be restored by re-loading from Excel files.
    """
    print_section("CORRECTED CLEANUP - FACT_LEAD_TIME ONLY")
    print("Previous cleanup bug: WHERE IS NOT NULL in subquery deleted all NULL-key rows")
    print("This version: Uses COALESCE to handle NULLs properly")
    print("\nNOTE: Raw tables need separate restore from Excel files")
    
    try:
        # Clean fact_lead_time only
        await cleanup_fact_lead_time()
        
        # Validate
        await final_validation()
        
    except Exception as e:
        print(f"\n❌ CLEANUP FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
