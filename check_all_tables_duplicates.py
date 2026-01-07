"""
COMPREHENSIVE DUPLICATE CHECK - ALL TABLES

Check every single table in database for duplicates:
- All fact tables
- All raw tables  
- All dimension tables
- Any other tables

Generate detailed report with:
- Business key definition for each table
- Current duplicate count
- Percentage of duplicates
- Sample duplicate records
"""

from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

print("="*80)
print("  COMPREHENSIVE DUPLICATE CHECK - ALL TABLES")
print("="*80)

# Define business keys for each table
TABLE_BUSINESS_KEYS = {
    # Fact tables
    'fact_billing': {
        'keys': ['billing_document', 'billing_item'],
        'description': 'Billing Document + Item'
    },
    'fact_production': {
        'keys': ['order_number', 'batch'],
        'description': 'Production Order + Batch'
    },
    'fact_delivery': {
        'keys': ['delivery', 'line_item'],
        'description': 'Delivery + Line Item'
    },
    'fact_ar_aging': {
        'keys': ['snapshot_date', 'customer_code', 'document_number'],
        'description': 'Snapshot Date + Customer + Document'
    },
    'fact_lead_time': {
        'keys': ['order_number', 'batch'],
        'description': 'Order Number + Batch'
    },
    'fact_alerts': {
        'keys': ['alert_type', 'reference_id', 'detected_at'],
        'description': 'Alert Type + Reference + Detected Time'
    },
    'fact_inventory': {
        'keys': ['material_code', 'plant_code', 'batch', 'movement_date'],
        'description': 'Material + Plant + Batch + Date'
    },
    'fact_purchase_order': {
        'keys': ['material', 'batch'],
        'description': 'Material + Batch'
    },
    'fact_target': {
        'keys': ['salesman_name', 'semester', 'year'],
        'description': 'Salesman + Semester + Year'
    },
    'fact_production_chain': {
        'keys': ['p03_batch', 'p02_batch', 'p01_batch'],
        'description': 'P03 + P02 + P01 Batches'
    },
    'fact_mto_orders': {
        'keys': ['sales_order', 'batch'],
        'description': 'Sales Order + Batch'
    },
    
    # Raw tables - use JSONB keys
    'raw_cooispi': {
        'keys': ["raw_data->>'Order'", "raw_data->>'Material'"],
        'description': 'Production Order + Material',
        'is_jsonb': True
    },
    'raw_mb51': {
        'keys': ["raw_data->>'Material Document'", "raw_data->>'Material Doc.Item'"],
        'description': 'Material Doc + Item',
        'is_jsonb': True
    },
    'raw_zrmm024': {
        'keys': ["raw_data->>'Material'", "raw_data->>'Batch'"],
        'description': 'Material + Batch',
        'is_jsonb': True
    },
    'raw_zrsd002': {
        'keys': ["raw_data->>'Billing Document'", "raw_data->>'Billing Item'"],
        'description': 'Billing Doc + Item',
        'is_jsonb': True
    },
    'raw_zrsd004': {
        'keys': ["raw_data->>'Delivery'", "raw_data->>'Item'"],
        'description': 'Delivery + Item',
        'is_jsonb': True
    },
    'raw_zrsd006': {
        'keys': ["raw_data->>'Sales Document'", "raw_data->>'Item'"],
        'description': 'Sales Doc + Item',
        'is_jsonb': True
    },
    'raw_zrfi005': {
        'keys': ["raw_data->>'Customer'", "raw_data->>'Document Number'"],
        'description': 'Customer + Document',
        'is_jsonb': True
    },
    'raw_target': {
        'keys': ["raw_data->>'Salesman Name'", "raw_data->>'Semester'", "raw_data->>'Year'"],
        'description': 'Salesman + Semester + Year',
        'is_jsonb': True
    },
    
    # Dimension tables
    'dim_material': {
        'keys': ['material_code'],
        'description': 'Material Code'
    },
    'dim_uom_conversion': {
        'keys': ['material_code'],
        'description': 'Material Code'
    },
    'dim_plant': {
        'keys': ['plant_code'],
        'description': 'Plant Code'
    },
    'dim_mvt': {
        'keys': ['mvt_code'],
        'description': 'Movement Type Code'
    },
    'dim_dist_channel': {
        'keys': ['dist_channel'],
        'description': 'Distribution Channel'
    },
}

with engine.connect() as conn:
    # Get all tables in database
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    
    print(f"\nFound {len(all_tables)} tables in database")
    print(f"Configured business keys for {len(TABLE_BUSINESS_KEYS)} tables\n")
    
    duplicate_summary = []
    
    for table_name in sorted(all_tables):
        # Skip system tables
        if table_name.startswith('pg_') or table_name in ['upload_history']:
            continue
        
        if table_name not in TABLE_BUSINESS_KEYS:
            print(f"\n⚠️  {table_name}: No business key defined - SKIPPING")
            continue
        
        config = TABLE_BUSINESS_KEYS[table_name]
        is_jsonb = config.get('is_jsonb', False)
        
        try:
            # Get total count
            total_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            if total_count == 0:
                print(f"\n📭 {table_name}: EMPTY (0 rows)")
                continue
            
            # Build DISTINCT count query
            if is_jsonb:
                # For JSONB keys, concatenate with || and COALESCE for NULLs
                key_concat = " || '-' || ".join([f"COALESCE({key}, '')" for key in config['keys']])
            else:
                # For regular columns
                key_concat = " || '-' || ".join([f"COALESCE(CAST({key} AS TEXT), '')" for key in config['keys']])
            
            unique_count = conn.execute(text(f"""
                SELECT COUNT(DISTINCT {key_concat})
                FROM {table_name}
            """)).scalar()
            
            duplicate_count = total_count - unique_count
            dup_pct = (duplicate_count / total_count * 100) if total_count > 0 else 0
            
            # Display result
            if duplicate_count > 0:
                print(f"\n❌ {table_name}:")
                print(f"   Total: {total_count:,} rows")
                print(f"   Unique: {unique_count:,}")
                print(f"   Duplicates: {duplicate_count:,} ({dup_pct:.1f}%)")
                print(f"   Business Key: {config['description']}")
                
                # Get sample duplicates
                if is_jsonb:
                    sample_query = f"""
                        SELECT {key_concat} as business_key, COUNT(*) as cnt
                        FROM {table_name}
                        GROUP BY {key_concat}
                        HAVING COUNT(*) > 1
                        ORDER BY cnt DESC
                        LIMIT 3
                    """
                else:
                    sample_query = f"""
                        SELECT {key_concat} as business_key, COUNT(*) as cnt
                        FROM {table_name}
                        GROUP BY {key_concat}
                        HAVING COUNT(*) > 1
                        ORDER BY cnt DESC
                        LIMIT 3
                    """
                
                samples = conn.execute(text(sample_query)).fetchall()
                if samples:
                    print(f"   Sample duplicates:")
                    for row in samples:
                        print(f"     - {row[0]}: {row[1]} times")
                
                duplicate_summary.append({
                    'table': table_name,
                    'total': total_count,
                    'duplicates': duplicate_count,
                    'pct': dup_pct
                })
            else:
                print(f"\n✅ {table_name}: {total_count:,} rows (NO DUPLICATES)")
        
        except Exception as e:
            print(f"\n⚠️  {table_name}: ERROR - {e}")
    
    # Summary
    print("\n" + "="*80)
    print("  SUMMARY - TABLES WITH DUPLICATES")
    print("="*80)
    
    if duplicate_summary:
        print(f"\nFound duplicates in {len(duplicate_summary)} tables:\n")
        for item in sorted(duplicate_summary, key=lambda x: x['duplicates'], reverse=True):
            print(f"  {item['table']}: {item['duplicates']:,} duplicates ({item['pct']:.1f}%)")
    else:
        print("\n✅ NO DUPLICATES FOUND IN ANY TABLE!")
    
    print("\n" + "="*80)
    print("  DUPLICATE CHECK COMPLETE")
    print("="*80)
