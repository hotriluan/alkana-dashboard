"""
COMPREHENSIVE BUSINESS KEY DUPLICATE CHECK
Check ALL tables for BUSINESS LOGIC duplicates (not just PK)
"""

from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

# Define BUSINESS KEYS for each table
BUSINESS_KEY_CONFIG = {
    # FACT TABLES - Business keys (not PK id)
    'fact_billing': {
        'keys': ['billing_document', 'billing_item'],
        'desc': 'Billing Document + Item'
    },
    'fact_production': {
        'keys': ['order_number', 'batch'],
        'desc': 'Production Order + Batch'
    },
    'fact_delivery': {
        'keys': ['delivery', 'line_item'],
        'desc': 'Delivery + Line Item'
    },
    'fact_ar_aging': {
        'keys': ['customer_code', 'document_number', 'company_code'],
        'desc': 'Customer + Document + Company'
    },
    'fact_lead_time': {
        'keys': ['order_number', 'batch'],
        'desc': 'Order + Batch'
    },
    'fact_alerts': {
        'keys': ['batch', 'alert_type'],
        'desc': 'Batch + Alert Type'
    },
    'fact_inventory': {
        'keys': ['material_code', 'plant_code', 'batch', 'storage_location'],
        'desc': 'Material + Plant + Batch + Location'
    },
    'fact_purchase_order': {
        'keys': ['order_number', 'material_code'],
        'desc': 'PO Number + Material'
    },
    'fact_target': {
        'keys': ['salesman_name', 'semester', 'year'],
        'desc': 'Salesman + Semester + Year'
    },
    'fact_p02_p01_yield': {
        'keys': ['p02_batch', 'p01_batch'],
        'desc': 'P02 + P01 Batch'
    },
    'fact_production_chain': {
        'keys': ['p03_batch'],
        'desc': 'P03 Batch'
    },
    
    # RAW TABLES - Use row_hash
    'raw_cooispi': {
        'keys': ['row_hash'],
        'desc': 'Row Hash'
    },
    'raw_mb51': {
        'keys': ['row_hash'],
        'desc': 'Row Hash'
    },
    'raw_zrmm024': {
        'keys': ['row_hash'],
        'desc': 'Row Hash'
    },
    'raw_zrsd002': {
        'keys': ['row_hash'],
        'desc': 'Row Hash'
    },
    'raw_zrsd004': {
        'keys': ['row_hash'],
        'desc': 'Row Hash'
    },
    'raw_zrsd006': {
        'keys': ['row_hash'],
        'desc': 'Row Hash'
    },
    'raw_zrfi005': {
        'keys': ['row_hash'],
        'desc': 'Row Hash'
    },
    'raw_target': {
        'keys': ['row_hash'],
        'desc': 'Row Hash'
    },
    
    # DIMENSION TABLES
    'dim_uom_conversion': {
        'keys': ['material_code'],
        'desc': 'Material Code'
    },
    'dim_plant': {
        'keys': ['plant_code'],
        'desc': 'Plant Code'
    },
    'dim_mvt': {
        'keys': ['mvt_code'],
        'desc': 'Movement Type'
    },
}

print("="*80)
print("  COMPREHENSIVE BUSINESS KEY DUPLICATE CHECK")
print("  Checking ALL tables for business logic duplicates")
print("="*80)

with engine.connect() as conn:
    inspector = inspect(engine)
    all_tables = sorted(inspector.get_table_names())
    
    print(f"\n📊 Total tables: {len(all_tables)}")
    print(f"📋 Configured business keys: {len(BUSINESS_KEY_CONFIG)}\n")
    
    results = {
        'clean': [],
        'duplicates': [],
        'empty': [],
        'skipped': []
    }
    
    for table_name in all_tables:
        # Skip system/auth tables
        if table_name in ['upload_history', 'users', 'roles', 'permissions', 
                          'user_roles', 'role_permissions'] or table_name.startswith('pg_'):
            results['skipped'].append(table_name)
            continue
        
        print(f"📋 {table_name}")
        
        try:
            # Check if empty
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            if count == 0:
                print(f"  📭 EMPTY (0 rows)\n")
                results['empty'].append(table_name)
                continue
            
            # Get business key config
            if table_name not in BUSINESS_KEY_CONFIG:
                print(f"  ⚠️  No business key configured - SKIPPED\n")
                results['skipped'].append(table_name)
                continue
            
            config = BUSINESS_KEY_CONFIG[table_name]
            keys = config['keys']
            desc = config['desc']
            
            # Verify columns exist
            columns = [c['name'] for c in inspector.get_columns(table_name)]
            missing = [k for k in keys if k not in columns]
            
            if missing:
                print(f"  ⚠️  Missing columns: {missing} - SKIPPED\n")
                results['skipped'].append(table_name)
                continue
            
            # Check for duplicates
            key_list = ', '.join(keys)
            
            result = conn.execute(text(f"""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT ({key_list})) as unique_count
                FROM {table_name}
            """))
            row = result.fetchone()
            total = row[0]
            unique = row[1]
            dupes = total - unique
            
            print(f"  Total: {total:,} rows")
            print(f"  Business Keys: {desc}")
            print(f"  Keys: {key_list}")
            
            if dupes > 0:
                pct = dupes / total * 100
                print(f"  ❌ DUPLICATES: {dupes:,} ({pct:.1f}%)")
                
                # Get top 3 duplicates
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
                    print(f"  Top duplicates:")
                    for sample in samples:
                        key_vals = ' | '.join([str(v) for v in sample[:-1]])
                        print(f"    • {key_vals}: {sample[-1]}x")
                
                results['duplicates'].append({
                    'table': table_name,
                    'total': total,
                    'duplicates': dupes,
                    'pct': pct,
                    'keys': key_list
                })
            else:
                print(f"  ✅ NO DUPLICATES")
                results['clean'].append(table_name)
            
            print()
            
        except Exception as e:
            print(f"  ⚠️  ERROR: {str(e)[:150]}\n")
            results['skipped'].append(table_name)
    
    # COMPREHENSIVE SUMMARY
    print("="*80)
    print("  SUMMARY REPORT")
    print("="*80)
    
    print(f"\n📊 Coverage:")
    print(f"  Total tables: {len(all_tables)}")
    print(f"  Checked: {len(results['clean']) + len(results['duplicates'])}")
    print(f"  Clean: {len(results['clean'])}")
    print(f"  Has duplicates: {len(results['duplicates'])}")
    print(f"  Empty: {len(results['empty'])}")
    print(f"  Skipped: {len(results['skipped'])}")
    
    if results['empty']:
        print(f"\n📭 Empty Tables ({len(results['empty'])}):")
        for t in results['empty']:
            print(f"  • {t}")
    
    if results['duplicates']:
        print(f"\n❌ TABLES WITH DUPLICATES ({len(results['duplicates'])}):")
        total_all_dupes = 0
        
        for item in sorted(results['duplicates'], key=lambda x: x['duplicates'], reverse=True):
            print(f"\n  {item['table']}:")
            print(f"    Total rows: {item['total']:,}")
            print(f"    Duplicates: {item['duplicates']:,} ({item['pct']:.1f}%)")
            print(f"    Business keys: {item['keys']}")
            total_all_dupes += item['duplicates']
        
        print(f"\n  📈 TOTAL DUPLICATE ROWS ACROSS ALL TABLES: {total_all_dupes:,}")
        
        # Action required
        print(f"\n  ⚠️  ACTION REQUIRED:")
        print(f"  Run fix_remaining_duplicates.py to remove {total_all_dupes:,} duplicate rows")
        print(f"  Then add UNIQUE constraints to prevent future duplicates")
        
    else:
        print(f"\n✅ PERFECT! NO BUSINESS LOGIC DUPLICATES IN ANY TABLE!")
        print(f"  All {len(results['clean'])} tables are clean")
    
    if results['skipped']:
        print(f"\n⚠️  Skipped Tables ({len(results['skipped'])}):")
        for t in results['skipped']:
            print(f"  • {t}")
    
    # DETAILED CLEAN TABLES
    if results['clean']:
        print(f"\n✅ Clean Tables ({len(results['clean'])}):")
        for t in results['clean']:
            print(f"  • {t}")
    
    print("\n" + "="*80)
    print("  AUDIT COMPLETE")
    print("="*80)
