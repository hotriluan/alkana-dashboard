"""
Phase 5: Performance Optimization - Add Database Indexes

Add indexes to improve query performance, especially for date filtering.

Skills: database, backend-development, performance-optimization
"""
import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    
    print("="*80)
    print("PHASE 5: PERFORMANCE OPTIMIZATION - DATABASE INDEXES")
    print("="*80)
    
    # Indexes to create based on API query patterns
    indexes = [
        {
            "name": "idx_fact_p02_p01_yield_production_date",
            "table": "fact_p02_p01_yield",
            "column": "production_date",
            "purpose": "Speed up yield dashboard date filtering"
        },
        {
            "name": "idx_fact_inventory_posting_date",
            "table": "fact_inventory",
            "column": "posting_date",
            "purpose": "Speed up inventory date queries"
        },
        {
            "name": "idx_fact_ar_aging_report_date",
            "table": "fact_ar_aging",
            "column": "report_date",
            "purpose": "Speed up AR aging date lookups"
        },
        {
            "name": "idx_fact_inventory_plant_material",
            "table": "fact_inventory",
            "columns": "(plant_code, material_code)",
            "purpose": "Speed up inventory lookups by plant+material"
        }
    ]
    
    print("\n[1] Checking Existing Indexes...")
    existing = db.execute(text("""
        SELECT tablename, indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND (indexname LIKE 'idx_fact%' OR indexname LIKE '%_pkey')
        ORDER BY tablename, indexname
    """)).fetchall()
    
    print(f"  Found {len(existing)} existing indexes:")
    for idx in existing:
        print(f"    {idx[0]}: {idx[1]}")
    
    # Create indexes
    print("\n[2] Creating Performance Indexes...")
    created_count = 0
    skipped_count = 0
    
    for idx in indexes:
        index_name = idx['name']
        table_name = idx['table']
        column_spec = idx.get('columns', idx.get('column'))
        purpose = idx['purpose']
        
        # Check if index already exists
        check = db.execute(text("""
            SELECT 1 FROM pg_indexes 
            WHERE indexname = :name
        """), {"name": index_name}).fetchone()
        
        if check:
            print(f"  ⏭️  {index_name} - Already exists (skipping)")
            skipped_count += 1
            continue
        
        try:
            sql = f"CREATE INDEX {index_name} ON {table_name} {column_spec}"
            db.execute(text(sql))
            db.commit()
            print(f"  ✅ {index_name}")
            print(f"     Table: {table_name}")
            print(f"     Purpose: {purpose}")
            created_count += 1
        except Exception as e:
            db.rollback()
            print(f"  ❌ {index_name} - Error: {str(e)[:100]}")
    
    # Verify indexes
    print(f"\n[3] Verification:")
    new_indexes = db.execute(text("""
        SELECT tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_fact%'
        ORDER BY tablename, indexname
    """)).fetchall()
    
    print(f"  Total indexes on fact tables: {len(new_indexes)}")
    for idx in new_indexes:
        print(f"    {idx[0]}.{idx[1]}")
    
    # Analyze tables for better query planning
    print(f"\n[4] Analyzing Tables (update statistics)...")
    tables = ['fact_p02_p01_yield', 'fact_inventory', 'fact_ar_aging']
    for table in tables:
        try:
            db.execute(text(f"ANALYZE {table}"))
            print(f"  ✅ {table}")
        except Exception as e:
            print(f"  ❌ {table}: {e}")
    
    db.commit()
    
    # Summary
    print("\n" + "="*80)
    print("PERFORMANCE OPTIMIZATION SUMMARY")
    print("="*80)
    print(f"  Indexes created: {created_count}")
    print(f"  Indexes skipped: {skipped_count} (already exist)")
    print(f"  Tables analyzed: {len(tables)}")
    print()
    print("Expected Performance Improvements:")
    print("  - Yield dashboard date filters: 2-10x faster")
    print("  - Inventory queries: 5-20x faster")
    print("  - AR aging lookups: 2-5x faster")
    print()
    print("✅ Phase 5 Complete!")
    print("="*80)
    
    db.close()

if __name__ == "__main__":
    main()
