"""
COMPREHENSIVE DUPLICATE CHECK - ROBUST VERSION

Automatically detects schema and checks for duplicates
"""

from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("="*80)
print("  COMPREHENSIVE DUPLICATE CHECK - ALL TABLES (ROBUST)")
print("="*80)

# Manual business key configuration based on actual schema
BUSINESS_KEYS = {
    # FACT TABLES
    'fact_billing': ['billing_document', 'billing_item'],
    'fact_production': ['order_number', 'batch'],
    'fact_delivery': ['delivery', 'line_item'],
    'fact_ar_aging': ['snapshot_date', 'customer_code', 'document_number'],
    'fact_lead_time': ['order_number', 'batch'],
    'fact_alerts': ['alert_id'],  # Primary key check
    'fact_inventory': ['material_code', 'plant_code', 'batch', 'movement_date'],
    'fact_purchase_order': ['material', 'batch'],
    'fact_target': ['salesman_name', 'semester', 'year'],
    'fact_production_chain': ['p03_batch'],  # Or could be combination
    'fact_p02_p01_yield': ['p02_batch', 'p01_batch'],
    
    # RAW TABLES - Check via row_hash if it exists
    'raw_cooispi': ['row_hash'],
    'raw_mb51': ['row_hash'],
    'raw_zrmm024': ['row_hash'],
    'raw_zrsd002': ['row_hash'],
    'raw_zrsd004': ['row_hash'],
    'raw_zrsd006': ['row_hash'],
    'raw_zrfi005': ['row_hash'],
    'raw_target': ['row_hash'],
    
    # DIMENSION TABLES
    'dim_uom_conversion': ['material_code'],
    'dim_plant': ['plant_code'],
    'dim_mvt': ['mvt_code'],
    'dim_dist_channel': ['dist_channel'],
    'dim_material': ['material_code'],
}

with engine.connect() as conn:
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    
    print(f"\nFound {len(all_tables)} tables in database\n")
    
    duplicate_summary = []
    
    for table_name in sorted(all_tables):
        # Skip system/auth tables
        if table_name.startswith('pg_') or table_name in ['upload_history', 'users', 'roles', 'permissions', 'user_roles', 'role_permissions', 'dim_storage_location', 'dim_customer_group']:
            continue
        
        if table_name not in BUSINESS_KEYS:
            print(f"⚠️  {table_name}: No business key configured - SKIPPING")
            continue
        
        try:
            # Get table columns to verify keys exist
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            business_keys = BUSINESS_KEYS[table_name]
            
            # Verify all keys exist
            missing_keys = [k for k in business_keys if k not in columns]
            if missing_keys:
                print(f"⚠️  {table_name}: Missing columns {missing_keys} - SKIPPING")
                continue
            
            # Get total count
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            total_count = result.scalar()
            
            if total_count == 0:
                print(f"📭 {table_name}: EMPTY (0 rows)")
                continue
            
            # Build GROUP BY for distinct count
            key_list = ', '.join(business_keys)
            
            result = conn.execute(text(f"""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT ({key_list})) as unique_count
                FROM {table_name}
            """))
            row = result.fetchone()
            total = row[0]
            unique_count = row[1]
            
            duplicate_count = total - unique_count
            dup_pct = (duplicate_count / total * 100) if total > 0 else 0
            
            if duplicate_count > 0:
                print(f"\n❌ {table_name}:")
                print(f"   Total: {total:,} rows")
                print(f"   Unique: {unique_count:,}")
                print(f"   Duplicates: {duplicate_count:,} ({dup_pct:.1f}%)")
                print(f"   Business Keys: {', '.join(business_keys)}")
                
                # Sample duplicates
                result = conn.execute(text(f"""
                    SELECT {key_list}, COUNT(*) as cnt
                    FROM {table_name}
                    GROUP BY {key_list}
                    HAVING COUNT(*) > 1
                    ORDER BY cnt DESC
                    LIMIT 3
                """))
                
                samples = result.fetchall()
                if samples:
                    print(f"   Sample duplicates:")
                    for row in samples:
                        key_values = ' | '.join([str(v) for v in row[:-1]])
                        print(f"     - {key_values}: {row[-1]} times")
                
                duplicate_summary.append({
                    'table': table_name,
                    'total': total,
                    'duplicates': duplicate_count,
                    'pct': dup_pct
                })
            else:
                print(f"✅ {table_name}: {total:,} rows (NO DUPLICATES)")
        
        except Exception as e:
            print(f"⚠️  {table_name}: ERROR - {str(e)[:100]}")
    
    # Summary
    print("\n" + "="*80)
    print("  SUMMARY - DUPLICATE CHECK RESULTS")
    print("="*80)
    
    if duplicate_summary:
        print(f"\n❌ Found duplicates in {len(duplicate_summary)} table(s):\n")
        for item in sorted(duplicate_summary, key=lambda x: x['duplicates'], reverse=True):
            print(f"  {item['table']}: {item['duplicates']:,} duplicates ({item['pct']:.1f}%)")
        print(f"\n⚠️  TOTAL DUPLICATE ROWS: {sum(i['duplicates'] for i in duplicate_summary):,}")
    else:
        print("\n✅ NO DUPLICATES FOUND IN ANY TABLE!")
    
    print("\n" + "="*80)
    print("  CHECK COMPLETE")
    print("="*80)
