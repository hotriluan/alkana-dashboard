"""
COMPREHENSIVE DATABASE TABLES AUDIT
Check ALL tables - no exceptions
Auto-detect schema for each table and check duplicates
"""

from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("="*80)
print("  COMPREHENSIVE DATABASE AUDIT - ALL TABLES")
print("="*80)

with engine.connect() as conn:
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    
    print(f"\n📊 Total tables in database: {len(all_tables)}\n")
    
    # List all tables first
    print("All tables:")
    for i, table in enumerate(sorted(all_tables), 1):
        print(f"  {i:2d}. {table}")
    
    print("\n" + "="*80)
    print("  DUPLICATE CHECK FOR EACH TABLE")
    print("="*80)
    
    results = {
        'checked': [],
        'clean': [],
        'has_duplicates': [],
        'empty': [],
        'no_pk': []
    }
    
    for table_name in sorted(all_tables):
        # Skip system tables
        if table_name.startswith('pg_'):
            continue
        
        print(f"\n📋 {table_name}")
        
        try:
            # Get row count
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            if count == 0:
                print(f"  📭 EMPTY (0 rows)")
                results['empty'].append(table_name)
                continue
            
            # Get columns
            columns = inspector.get_columns(table_name)
            col_names = [c['name'] for c in columns]
            
            # Get primary key
            pk = inspector.get_pk_constraint(table_name)
            pk_columns = pk.get('constrained_columns', []) if pk else []
            
            # Get unique constraints
            unique_constraints = inspector.get_unique_constraints(table_name)
            
            # Determine business keys
            if pk_columns:
                business_keys = pk_columns
                key_source = "PRIMARY KEY"
            elif unique_constraints:
                business_keys = unique_constraints[0]['column_names']
                key_source = "UNIQUE CONSTRAINT"
            elif 'row_hash' in col_names:
                business_keys = ['row_hash']
                key_source = "row_hash"
            elif 'id' in col_names:
                # Use id as fallback - check if truly unique
                business_keys = ['id']
                key_source = "id (fallback)"
            else:
                # No obvious key - check all columns
                print(f"  ⚠️  No PK/unique constraint - checking ALL columns")
                results['no_pk'].append(table_name)
                
                # Check if ALL columns together form unique rows
                col_list = ', '.join([f'CAST({c} AS TEXT)' for c in col_names if c != 'id'])
                if col_list:
                    result = conn.execute(text(f"""
                        SELECT COUNT(*) as total,
                               COUNT(DISTINCT ({col_list})) as unique_count
                        FROM {table_name}
                    """))
                    row = result.fetchone()
                    total = row[0]
                    unique = row[1]
                    dupes = total - unique
                    
                    print(f"  Rows: {total:,}")
                    print(f"  Unique: {unique:,}")
                    
                    if dupes > 0:
                        print(f"  ❌ {dupes:,} duplicates ({dupes/total*100:.1f}%)")
                        results['has_duplicates'].append({
                            'table': table_name,
                            'duplicates': dupes,
                            'total': total
                        })
                    else:
                        print(f"  ✅ NO DUPLICATES")
                        results['clean'].append(table_name)
                    
                    results['checked'].append(table_name)
                continue
            
            # Check for duplicates using business keys
            key_list = ', '.join(business_keys)
            
            result = conn.execute(text(f"""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT ({key_list})) as unique_count
                FROM {table_name}
            """))
            row = result.fetchone()
            total = row[0]
            unique = row[1]
            dupes = total - unique
            
            print(f"  Rows: {total:,}")
            print(f"  Business Keys: {key_list} ({key_source})")
            
            if dupes > 0:
                print(f"  ❌ DUPLICATES FOUND: {dupes:,} ({dupes/total*100:.1f}%)")
                
                # Get sample duplicates
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
                    print(f"  Sample duplicates:")
                    for sample in samples:
                        key_val = ' | '.join([str(v) for v in sample[:-1]])
                        print(f"    - {key_val}: {sample[-1]} times")
                
                results['has_duplicates'].append({
                    'table': table_name,
                    'duplicates': dupes,
                    'total': total,
                    'keys': key_list
                })
            else:
                print(f"  ✅ NO DUPLICATES")
                results['clean'].append(table_name)
            
            results['checked'].append(table_name)
            
        except Exception as e:
            print(f"  ⚠️  ERROR: {str(e)[:100]}")
    
    # SUMMARY
    print("\n" + "="*80)
    print("  SUMMARY")
    print("="*80)
    
    print(f"\n📊 Statistics:")
    print(f"  Total tables: {len(all_tables)}")
    print(f"  Checked: {len(results['checked'])}")
    print(f"  Clean (no duplicates): {len(results['clean'])}")
    print(f"  Empty tables: {len(results['empty'])}")
    print(f"  Tables without PK: {len(results['no_pk'])}")
    print(f"  Tables with duplicates: {len(results['has_duplicates'])}")
    
    if results['empty']:
        print(f"\n📭 Empty tables ({len(results['empty'])}):")
        for t in results['empty']:
            print(f"  - {t}")
    
    if results['no_pk']:
        print(f"\n⚠️  Tables without PK/unique constraint ({len(results['no_pk'])}):")
        for t in results['no_pk']:
            print(f"  - {t}")
    
    if results['has_duplicates']:
        print(f"\n❌ Tables with duplicates ({len(results['has_duplicates'])}):")
        total_dupes = 0
        for item in sorted(results['has_duplicates'], key=lambda x: x['duplicates'], reverse=True):
            print(f"  - {item['table']}: {item['duplicates']:,} duplicates ({item['duplicates']/item['total']*100:.1f}%)")
            if 'keys' in item:
                print(f"    Keys: {item['keys']}")
            total_dupes += item['duplicates']
        
        print(f"\n  📈 TOTAL DUPLICATE ROWS: {total_dupes:,}")
    else:
        print(f"\n✅ NO DUPLICATES FOUND IN ANY TABLE!")
    
    print("\n" + "="*80)
    print("  AUDIT COMPLETE")
    print("="*80)
