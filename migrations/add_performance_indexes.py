"""
Performance Optimization: Add Database Indexes
Created: 2026-02-06
Purpose: Add composite indexes for heavily queried tables to improve ETL transform performance

Expected Impact:
- RawMb51 queries: 5-10x faster on filtered scans
- FactProduction lookups: 3-5x faster
- FactAlert lookups: 3-5x faster
- FactBilling channel lookups: 2-3x faster

Total transform time reduction: ~50-70% for large datasets
"""

from sqlalchemy import create_engine, text
import sys

def add_indexes(database_url: str, dry_run: bool = False):
    """
    Add performance indexes to database
    
    Args:
        database_url: PostgreSQL connection string
        dry_run: If True, only print SQL without executing
    """
    engine = create_engine(database_url)
    
    # Index creation statements
    indexes = [
        # RawMb51 - Most critical (queried multiple times in transform_lead_time)
        {
            'name': 'idx_mb51_mvt_batch',
            'table': 'raw_mb51',
            'columns': '(col_1_mvt_type, col_6_batch)',
            'reason': 'Optimizes MVT type + batch filtering (used 4x in transform_lead_time)'
        },
        {
            'name': 'idx_mb51_mvt_plant',
            'table': 'raw_mb51',
            'columns': '(col_1_mvt_type, col_2_plant)',
            'reason': 'Optimizes DC receipt queries (MVT 101 @ plant 1401)'
        },
        {
            'name': 'idx_mb51_posting_date',
            'table': 'raw_mb51',
            'columns': '(col_0_posting_date)',
            'reason': 'Optimizes date-based aggregations (MIN/MAX posting_date)'
        },
        {
            'name': 'idx_mb51_batch',
            'table': 'raw_mb51',
            'columns': '(col_6_batch)',
            'reason': 'Optimizes batch lookups and grouping operations'
        },
        {
            'name': 'idx_mb51_purchase_order',
            'table': 'raw_mb51',
            'columns': '(col_15_purchase_order)',
            'reason': 'Optimizes purchase order joins in transform_lead_time'
        },
        
        # FactProduction - Used in transform_cooispi for existence checks
        {
            'name': 'idx_production_order_plant',
            'table': 'fact_production',
            'columns': '(order_number, plant_code)',
            'reason': 'Optimizes row-by-row existence checks in transform_cooispi'
        },
        
        # FactBilling - Channel lookup in transform_lead_time
        {
            'name': 'idx_billing_so_channel',
            'table': 'fact_billing',
            'columns': '(so_number, dist_channel)',
            'reason': 'Optimizes sales order channel lookups'
        },
        
        # FactAlert - Duplicate detection in detect_alerts
        {
            'name': 'idx_alert_type_entity',
            'table': 'fact_alerts',
            'columns': '(alert_type, entity_id)',
            'reason': 'Optimizes alert existence checks (prevents duplicate alerts)'
        },
    ]
    
    print("=" * 80)
    print("PERFORMANCE INDEX CREATION")
    print("=" * 80)
    print()
    
    if dry_run:
        print("🔍 DRY RUN MODE - SQL will be printed but not executed")
        print()
    
    with engine.connect() as conn:
        for idx in indexes:
            sql = f"CREATE INDEX IF NOT EXISTS {idx['name']} ON {idx['table']} {idx['columns']}"
            
            print(f"📋 {idx['name']}")
            print(f"   Table: {idx['table']}")
            print(f"   Columns: {idx['columns']}")
            print(f"   Reason: {idx['reason']}")
            print(f"   SQL: {sql}")
            
            if not dry_run:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print("   ✅ Created successfully")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print("   ℹ️  Already exists (skipped)")
                    else:
                        print(f"   ❌ Error: {e}")
                        raise
            else:
                print("   ⏭️  Skipped (dry run)")
            
            print()
    
    print("=" * 80)
    if dry_run:
        print("✅ DRY RUN COMPLETE - No indexes were created")
    else:
        print("✅ ALL INDEXES CREATED SUCCESSFULLY")
        print()
        print("📊 To verify indexes:")
        print("   SELECT tablename, indexname FROM pg_indexes")
        print("   WHERE tablename IN ('raw_mb51', 'fact_production', 'fact_billing', 'fact_alerts');")
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Add performance indexes to database')
    parser.add_argument('--database-url', 
                       default='postgresql://postgres:password123@localhost:5432/alkana_dashboard',
                       help='Database connection string')
    parser.add_argument('--dry-run', action='store_true',
                       help='Print SQL without executing')
    parser.add_argument('--production', action='store_true',
                       help='Use production database credentials')
    
    args = parser.parse_args()
    
    # Production database URL
    if args.production:
        database_url = 'postgresql://alkana_user:Alkana2026SecureDB!@postgres:5432/alkana_dashboard'
    else:
        database_url = args.database_url
    
    print(f"🔗 Database: {database_url.split('@')[1] if '@' in database_url else database_url}")
    print()
    
    add_indexes(database_url, dry_run=args.dry_run)
