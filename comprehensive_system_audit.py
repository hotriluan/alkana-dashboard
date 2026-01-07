"""
COMPREHENSIVE SYSTEM-WIDE DATA AUDIT
Skills: data-analysis, databases, debugging, ETL, problem-solving
Claude Kit: Systematic investigation, DRY, KISS

Investigates ALL raw and fact tables for duplicate data issues
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import pandas as pd
from pathlib import Path

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alkana_db")
engine = create_engine(DATABASE_URL)

print("="*80)
print("COMPREHENSIVE SYSTEM-WIDE DATA AUDIT")
print("="*80)
print("\nChecking ALL raw and fact tables for duplicates and data quality issues...")

# ============================================================================
# PART 1: RAW TABLES AUDIT
# ============================================================================
print("\n" + "="*80)
print("PART 1: RAW TABLES AUDIT")
print("="*80)

raw_tables = [
    'raw_cooispi',
    'raw_mb51', 
    'raw_zrmm024',
    'raw_zrsd002',
    'raw_zrsd004',
    'raw_zrsd006',
    'raw_zrfi005'
]

raw_results = {}

for table in raw_tables:
    print(f"\n{'='*80}")
    print(f"Checking {table.upper()}")
    print(f"{'='*80}")
    
    try:
        with engine.connect() as conn:
            # Get row count
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            total_rows = result.fetchone()[0]
            
            print(f"  Total rows: {total_rows:,}")
            
            if total_rows == 0:
                print(f"  ⚠ WARNING: Empty table!")
                raw_results[table] = {'status': 'EMPTY', 'rows': 0, 'duplicates': 0}
                continue
            
            # Check for duplicates based on common key patterns
            # Different tables have different keys
            dup_query = None
            
            if table == 'raw_cooispi':
                # Production orders - check by order number + operation
                dup_query = """
                    SELECT COUNT(*) - COUNT(DISTINCT (raw_data->>'Order', raw_data->>'Operation'))
                    FROM {table}
                """
            elif table == 'raw_mb51':
                # Material movements - check by material doc + item
                dup_query = """
                    SELECT COUNT(*) - COUNT(DISTINCT (raw_data->>'Material Document', raw_data->>'Item'))
                    FROM {table}
                """
            elif table == 'raw_zrmm024':
                # Stock - check by material + plant + sloc
                dup_query = """
                    SELECT COUNT(*) - COUNT(DISTINCT (raw_data->>'Material', raw_data->>'Plant', raw_data->>'SLoc'))
                    FROM {table}
                """
            elif table == 'raw_zrsd002':
                # Billing - already checked
                dup_query = """
                    SELECT COUNT(*) - COUNT(DISTINCT (raw_data->>'Billing Document', raw_data->>'Billing Item'))
                    FROM {table}
                """
            elif table == 'raw_zrsd004':
                # Delivery - check by delivery + item
                dup_query = """
                    SELECT COUNT(*) - COUNT(DISTINCT (raw_data->>'Delivery', raw_data->>'Item'))
                    FROM {table}
                """
            elif table == 'raw_zrsd006':
                # Sales orders - check by SO + item
                dup_query = """
                    SELECT COUNT(*) - COUNT(DISTINCT (raw_data->>'Sales Document', raw_data->>'Item'))
                    FROM {table}
                """
            elif table == 'raw_zrfi005':
                # AR - check by customer + snapshot date
                dup_query = """
                    SELECT COUNT(*) - COUNT(DISTINCT (raw_data->>'Customer Name', raw_data->>'Snapshot Date'))
                    FROM {table}
                """
            
            if dup_query:
                result2 = conn.execute(text(dup_query.format(table=table)))
                duplicate_count = result2.fetchone()[0] or 0
                
                if duplicate_count > 0:
                    dup_pct = (duplicate_count / total_rows * 100)
                    print(f"  ❌ DUPLICATES FOUND: {duplicate_count:,} ({dup_pct:.1f}%)")
                    raw_results[table] = {'status': 'HAS_DUPLICATES', 'rows': total_rows, 'duplicates': duplicate_count}
                else:
                    print(f"  ✓ No duplicates found")
                    raw_results[table] = {'status': 'OK', 'rows': total_rows, 'duplicates': 0}
                    
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)[:100]}")
        raw_results[table] = {'status': 'ERROR', 'error': str(e)[:100]}

# ============================================================================
# PART 2: FACT TABLES AUDIT
# ============================================================================
print("\n" + "="*80)
print("PART 2: FACT TABLES AUDIT")
print("="*80)

fact_tables = {
    'fact_production': {
        'key': 'order_number',
        'date': 'actual_finish_date',
        'desc': 'Production Orders'
    },
    'fact_billing': {
        'key': 'billing_document, billing_item',
        'date': 'billing_date',
        'desc': 'Billing Documents'
    },
    'fact_delivery': {
        'key': 'delivery_number, delivery_item',
        'date': 'actual_gi_date',
        'desc': 'Delivery Documents'
    },
    'fact_ar_aging': {
        'key': 'customer_name, snapshot_date',
        'date': 'snapshot_date',
        'desc': 'AR Aging'
    },
    'fact_lead_time': {
        'key': 'order_number, batch',
        'date': 'end_date',
        'desc': 'Lead Time Analysis'
    },
    'fact_alerts': {
        'key': 'id',
        'date': 'detected_at',
        'desc': 'System Alerts'
    }
}

fact_results = {}

for table, info in fact_tables.items():
    print(f"\n{'='*80}")
    print(f"Checking {table.upper()} - {info['desc']}")
    print(f"{'='*80}")
    
    try:
        with engine.connect() as conn:
            # Get basic stats
            result = conn.execute(text(f"""
                SELECT 
                    COUNT(*) as total_rows,
                    MIN({info['date']}) as min_date,
                    MAX({info['date']}) as max_date
                FROM {table}
            """))
            row = result.fetchone()
            total_rows = row[0]
            min_date = row[1]
            max_date = row[2]
            
            print(f"  Total rows: {total_rows:,}")
            if min_date and max_date:
                print(f"  Date range: {min_date} to {max_date}")
            
            if total_rows == 0:
                print(f"  ⚠ WARNING: Empty table!")
                fact_results[table] = {'status': 'EMPTY', 'rows': 0}
                continue
            
            # Check for duplicates
            if ',' in info['key']:  # Composite key
                keys = info['key'].split(', ')
                result2 = conn.execute(text(f"""
                    SELECT COUNT(*) - COUNT(DISTINCT ({info['key']}))
                    FROM {table}
                """))
            else:  # Single key
                result2 = conn.execute(text(f"""
                    SELECT COUNT(*) - COUNT(DISTINCT {info['key']})
                    FROM {table}
                """))
            
            duplicate_count = result2.fetchone()[0] or 0
            
            if duplicate_count > 0:
                dup_pct = (duplicate_count / total_rows * 100)
                print(f"  ❌ DUPLICATES FOUND: {duplicate_count:,} ({dup_pct:.1f}%)")
                
                # Show sample duplicates
                if ',' in info['key']:
                    keys = info['key'].split(', ')
                    group_by = ', '.join(keys)
                    result3 = conn.execute(text(f"""
                        SELECT {group_by}, COUNT(*) as cnt
                        FROM {table}
                        GROUP BY {group_by}
                        HAVING COUNT(*) > 1
                        ORDER BY cnt DESC
                        LIMIT 3
                    """))
                    print(f"  Top duplicates:")
                    for dup in result3:
                        print(f"    - {dup[:-1]}: {dup[-1]} times")
                
                fact_results[table] = {'status': 'HAS_DUPLICATES', 'rows': total_rows, 'duplicates': duplicate_count}
            else:
                print(f"  ✓ No duplicates found")
                fact_results[table] = {'status': 'OK', 'rows': total_rows, 'duplicates': 0}
                
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)[:100]}")
        fact_results[table] = {'status': 'ERROR', 'error': str(e)[:100]}

# ============================================================================
# PART 3: EXCEL FILE COMPARISON
# ============================================================================
print("\n" + "="*80)
print("PART 3: EXCEL FILE COMPARISON")
print("="*80)

excel_files = list(Path('demodata').glob('*.xlsx'))
print(f"\nFound {len(excel_files)} Excel files in demodata/")

excel_comparison = {}

for excel_file in excel_files:
    print(f"\n📄 {excel_file.name}")
    try:
        df = pd.read_excel(excel_file)
        excel_rows = len(df)
        print(f"   Excel rows: {excel_rows:,}")
        
        # Try to match with database tables
        file_name = excel_file.stem.lower()
        
        # Find corresponding raw table
        raw_table = f"raw_{file_name}"
        if raw_table in raw_results:
            db_rows = raw_results[raw_table]['rows']
            diff = db_rows - excel_rows
            diff_pct = (diff / excel_rows * 100) if excel_rows > 0 else 0
            
            print(f"   DB rows ({raw_table}): {db_rows:,}")
            print(f"   Difference: {diff:+,} ({diff_pct:+.1f}%)")
            
            if abs(diff_pct) > 1:
                print(f"   ❌ MISMATCH: >1% difference!")
                excel_comparison[excel_file.name] = 'MISMATCH'
            else:
                print(f"   ✓ Matches within tolerance")
                excel_comparison[excel_file.name] = 'OK'
        else:
            print(f"   ⚠ No matching raw table found")
            excel_comparison[excel_file.name] = 'NO_TABLE'
            
    except Exception as e:
        print(f"   ❌ Error reading: {str(e)[:100]}")
        excel_comparison[excel_file.name] = 'ERROR'

# ============================================================================
# SUMMARY REPORT
# ============================================================================
print("\n" + "="*80)
print("SUMMARY REPORT")
print("="*80)

print("\n📊 RAW TABLES:")
issues_raw = []
for table, result in raw_results.items():
    status = result['status']
    if status == 'HAS_DUPLICATES':
        print(f"  ❌ {table}: {result['duplicates']:,} duplicates ({result['duplicates']/result['rows']*100:.1f}%)")
        issues_raw.append(table)
    elif status == 'EMPTY':
        print(f"  ⚠ {table}: EMPTY")
    elif status == 'OK':
        print(f"  ✓ {table}: OK ({result['rows']:,} rows)")
    else:
        print(f"  ❌ {table}: ERROR")

print("\n📊 FACT TABLES:")
issues_fact = []
for table, result in fact_results.items():
    status = result.get('status')
    if status == 'HAS_DUPLICATES':
        print(f"  ❌ {table}: {result['duplicates']:,} duplicates ({result['duplicates']/result['rows']*100:.1f}%)")
        issues_fact.append(table)
    elif status == 'EMPTY':
        print(f"  ⚠ {table}: EMPTY")
    elif status == 'OK':
        print(f"  ✓ {table}: OK ({result['rows']:,} rows)")
    else:
        print(f"  ❌ {table}: ERROR")

print("\n📊 EXCEL COMPARISONS:")
for file, status in excel_comparison.items():
    if status == 'MISMATCH':
        print(f"  ❌ {file}: Row count mismatch")
    elif status == 'OK':
        print(f"  ✓ {file}: Matches database")
    else:
        print(f"  ⚠ {file}: {status}")

# Final verdict
print("\n" + "="*80)
if issues_raw or issues_fact:
    print("❌ ISSUES FOUND - ACTION REQUIRED")
    print("="*80)
    if issues_raw:
        print(f"\nRaw tables with duplicates: {', '.join(issues_raw)}")
    if issues_fact:
        print(f"\nFact tables with duplicates: {', '.join(issues_fact)}")
    print("\nRecommendation: Run cleanup script for affected tables")
else:
    print("✅ ALL TABLES VALIDATED - NO CRITICAL ISSUES")
    print("="*80)

print("\nAudit completed successfully!")
