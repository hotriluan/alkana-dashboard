"""
Comprehensive cleanup script to remove duplicates from ALL affected tables
Based on audit findings showing 6 raw tables + 1 fact table with duplicates
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/alkana_dashboard")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

async def cleanup_raw_cooispi():
    """
    Cleanup raw_cooispi duplicates
    Business key: production_order + material_number
    """
    print_section("CLEANING RAW_COOISPI")
    
    session = Session()
    try:
        # Count before
        before_count = session.execute(text("""
            SELECT COUNT(*) FROM raw_cooispi
        """)).scalar()
        print(f"Before: {before_count:,} rows")
        
        # Find duplicates
        dup_count = session.execute(text("""
            SELECT 
                raw_data->>'Order' as order_num,
                raw_data->>'Material' as material,
                COUNT(*) as cnt
            FROM raw_cooispi
            WHERE raw_data->>'Order' IS NOT NULL 
              AND raw_data->>'Material' IS NOT NULL
            GROUP BY raw_data->>'Order', raw_data->>'Material'
            HAVING COUNT(*) > 1
        """)).fetchall()
        print(f"Found {len(dup_count)} duplicate combinations")
        
        # Delete duplicates keeping MIN(id)
        delete_result = session.execute(text("""
            DELETE FROM raw_cooispi
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM raw_cooispi
                WHERE raw_data->>'Order' IS NOT NULL 
                  AND raw_data->>'Material' IS NOT NULL
                GROUP BY raw_data->>'Order', raw_data->>'Material'
            )
        """))
        session.commit()
        
        # Count after
        after_count = session.execute(text("""
            SELECT COUNT(*) FROM raw_cooispi
        """)).scalar()
        print(f"After: {after_count:,} rows")
        print(f"✓ Removed {before_count - after_count:,} duplicate rows")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

async def cleanup_raw_mb51():
    """
    Cleanup raw_mb51 duplicates
    Business key: material_document + material_doc_item + material_number + movement_type
    """
    print_section("CLEANING RAW_MB51")
    
    session = Session()
    try:
        before_count = session.execute(text("SELECT COUNT(*) FROM raw_mb51")).scalar()
        print(f"Before: {before_count:,} rows")
        
        # Delete duplicates
        delete_result = session.execute(text("""
            DELETE FROM raw_mb51
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM raw_mb51
                WHERE raw_data->>'Material Document' IS NOT NULL
                  AND raw_data->>'Material Doc.Item' IS NOT NULL
                  AND raw_data->>'Material' IS NOT NULL
                  AND raw_data->>'Movement Type' IS NOT NULL
                GROUP BY 
                    raw_data->>'Material Document',
                    raw_data->>'Material Doc.Item',
                    raw_data->>'Material',
                    raw_data->>'Movement Type'
            )
        """))
        session.commit()
        
        after_count = session.execute(text("SELECT COUNT(*) FROM raw_mb51")).scalar()
        print(f"After: {after_count:,} rows")
        print(f"✓ Removed {before_count - after_count:,} duplicate rows")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

async def cleanup_raw_zrmm024():
    """
    Cleanup raw_zrmm024 duplicates
    Business key: material_number + batch_number
    """
    print_section("CLEANING RAW_ZRMM024")
    
    session = Session()
    try:
        before_count = session.execute(text("SELECT COUNT(*) FROM raw_zrmm024")).scalar()
        print(f"Before: {before_count:,} rows")
        
        delete_result = session.execute(text("""
            DELETE FROM raw_zrmm024
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM raw_zrmm024
                WHERE raw_data->>'Material' IS NOT NULL
                  AND raw_data->>'Batch' IS NOT NULL
                GROUP BY 
                    raw_data->>'Material',
                    raw_data->>'Batch'
            )
        """))
        session.commit()
        
        after_count = session.execute(text("SELECT COUNT(*) FROM raw_zrmm024")).scalar()
        print(f"After: {after_count:,} rows")
        print(f"✓ Removed {before_count - after_count:,} duplicate rows")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

async def cleanup_raw_zrsd004():
    """
    Cleanup raw_zrsd004 duplicates
    Business key: delivery_number + delivery_item
    """
    print_section("CLEANING RAW_ZRSD004")
    
    session = Session()
    try:
        before_count = session.execute(text("SELECT COUNT(*) FROM raw_zrsd004")).scalar()
        print(f"Before: {before_count:,} rows")
        
        delete_result = session.execute(text("""
            DELETE FROM raw_zrsd004
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM raw_zrsd004
                WHERE raw_data->>'Delivery' IS NOT NULL
                  AND raw_data->>'Item' IS NOT NULL
                GROUP BY 
                    raw_data->>'Delivery',
                    raw_data->>'Item'
            )
        """))
        session.commit()
        
        after_count = session.execute(text("SELECT COUNT(*) FROM raw_zrsd004")).scalar()
        print(f"After: {after_count:,} rows")
        print(f"✓ Removed {before_count - after_count:,} duplicate rows")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

async def cleanup_raw_zrsd006():
    """
    Cleanup raw_zrsd006 duplicates
    Business key: sales_order + so_item
    """
    print_section("CLEANING RAW_ZRSD006")
    
    session = Session()
    try:
        before_count = session.execute(text("SELECT COUNT(*) FROM raw_zrsd006")).scalar()
        print(f"Before: {before_count:,} rows")
        
        delete_result = session.execute(text("""
            DELETE FROM raw_zrsd006
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM raw_zrsd006
                WHERE raw_data->>'Sales Document' IS NOT NULL
                  AND raw_data->>'Item' IS NOT NULL
                GROUP BY 
                    raw_data->>'Sales Document',
                    raw_data->>'Item'
            )
        """))
        session.commit()
        
        after_count = session.execute(text("SELECT COUNT(*) FROM raw_zrsd006")).scalar()
        print(f"After: {after_count:,} rows")
        print(f"✓ Removed {before_count - after_count:,} duplicate rows")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

async def cleanup_raw_zrfi005():
    """
    Cleanup raw_zrfi005 duplicates
    Business key: customer_number + document_number
    """
    print_section("CLEANING RAW_ZRFI005")
    
    session = Session()
    try:
        before_count = session.execute(text("SELECT COUNT(*) FROM raw_zrfi005")).scalar()
        print(f"Before: {before_count:,} rows")
        
        delete_result = session.execute(text("""
            DELETE FROM raw_zrfi005
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM raw_zrfi005
                WHERE raw_data->>'Customer' IS NOT NULL
                  AND raw_data->>'Document Number' IS NOT NULL
                GROUP BY 
                    raw_data->>'Customer',
                    raw_data->>'Document Number'
            )
        """))
        session.commit()
        
        after_count = session.execute(text("SELECT COUNT(*) FROM raw_zrfi005")).scalar()
        print(f"After: {after_count:,} rows")
        print(f"✓ Removed {before_count - after_count:,} duplicate rows")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

async def cleanup_fact_lead_time():
    """
    Cleanup fact_lead_time duplicates
    Business key: sales_order + batch_number
    """
    print_section("CLEANING FACT_LEAD_TIME")
    
    session = Session()
    try:
        before_count = session.execute(text("SELECT COUNT(*) FROM fact_lead_time")).scalar()
        print(f"Before: {before_count:,} rows")
        
        # Show sample duplicates
        samples = session.execute(text("""
            SELECT sales_order, batch_number, COUNT(*) as cnt
            FROM fact_lead_time
            GROUP BY sales_order, batch_number
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 5
        """)).fetchall()
        
        if samples:
            print("\nSample duplicates:")
            for row in samples:
                print(f"  - SO {row[0]}, Batch {row[1]}: {row[2]} times")
        
        # Delete duplicates keeping MIN(id)
        delete_result = session.execute(text("""
            DELETE FROM fact_lead_time
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM fact_lead_time
                GROUP BY sales_order, batch_number
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

async def retransform_affected_tables():
    """
    Re-transform fact tables that were affected by raw data cleanup
    """
    print_section("RE-TRANSFORMING FACT TABLES")
    
    session = Session()
    try:
        # Import transform module
        sys.path.insert(0, 'src')
        from etl.transform import Transform
        
        transform = Transform()
        
        # Re-transform production (from raw_cooispi + raw_mb51)
        print("\n📊 Re-transforming fact_production...")
        session.execute(text("DELETE FROM fact_production"))
        session.commit()
        
        from models.models import RawCOOISPI, FactProduction
        raw_orders = session.query(RawCOOISPI).all()
        for raw in raw_orders:
            fact = transform.transform_production(raw)
            if fact:
                session.add(fact)
        session.commit()
        
        prod_count = session.execute(text("SELECT COUNT(*) FROM fact_production")).scalar()
        print(f"✓ fact_production: {prod_count:,} rows")
        
        # Re-transform delivery (from raw_zrsd004)
        print("\n📊 Re-transforming fact_delivery...")
        session.execute(text("DELETE FROM fact_delivery"))
        session.commit()
        
        from models.models import RawZRSD004
        raw_deliveries = session.query(RawZRSD004).all()
        for raw in raw_deliveries:
            fact = transform.transform_delivery(raw)
            if fact:
                session.add(fact)
        session.commit()
        
        del_count = session.execute(text("SELECT COUNT(*) FROM fact_delivery")).scalar()
        print(f"✓ fact_delivery: {del_count:,} rows")
        
        # Re-transform AR aging (from raw_zrfi005)
        print("\n📊 Re-transforming fact_ar_aging...")
        session.execute(text("DELETE FROM fact_ar_aging"))
        session.commit()
        
        from models.models import RawZRFI005
        raw_ar = session.query(RawZRFI005).all()
        for raw in raw_ar:
            fact = transform.transform_ar_aging(raw)
            if fact:
                session.add(fact)
        session.commit()
        
        ar_count = session.execute(text("SELECT COUNT(*) FROM fact_ar_aging")).scalar()
        print(f"✓ fact_ar_aging: {ar_count:,} rows")
        
        # Note: fact_lead_time already cleaned directly, no retransform needed
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error during retransform: {e}")
        raise
    finally:
        session.close()

async def final_validation():
    """
    Validate all tables after cleanup
    """
    print_section("FINAL VALIDATION")
    
    session = Session()
    try:
        # Check all raw tables
        tables = [
            'raw_cooispi',
            'raw_mb51', 
            'raw_zrmm024',
            'raw_zrsd004',
            'raw_zrsd006',
            'raw_zrfi005'
        ]
        
        print("\n📊 RAW TABLES:")
        for table in tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table}: {count:,} rows")
        
        # Check fact tables
        fact_tables = [
            'fact_production',
            'fact_billing',
            'fact_delivery',
            'fact_ar_aging',
            'fact_lead_time',
            'fact_alerts'
        ]
        
        print("\n📊 FACT TABLES:")
        for table in fact_tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table}: {count:,} rows")
        
        print("\n✅ Cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
    finally:
        session.close()

async def main():
    """
    Main execution flow
    """
    print_section("COMPREHENSIVE CLEANUP - ALL TABLES")
    print("This will remove duplicates from 6 raw tables + 1 fact table")
    print("and re-transform affected fact tables")
    
    try:
        # Step 1: Clean raw tables
        print("\n" + "="*80)
        print("STEP 1: CLEANING RAW TABLES")
        print("="*80)
        await cleanup_raw_cooispi()
        await cleanup_raw_mb51()
        await cleanup_raw_zrmm024()
        await cleanup_raw_zrsd004()
        await cleanup_raw_zrsd006()
        await cleanup_raw_zrfi005()
        
        # Step 2: Clean fact tables
        print("\n" + "="*80)
        print("STEP 2: CLEANING FACT TABLES")
        print("="*80)
        await cleanup_fact_lead_time()
        
        # Step 3: Re-transform affected tables
        print("\n" + "="*80)
        print("STEP 3: RE-TRANSFORMING AFFECTED TABLES")
        print("="*80)
        await retransform_affected_tables()
        
        # Step 4: Validate
        await final_validation()
        
    except Exception as e:
        print(f"\n❌ CLEANUP FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
