"""
Data Discrepancy Diagnostic Tool
Compares Excel source files vs Database vs Dashboard
"""
import os
import sys
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def connect_db():
    """Connect to PostgreSQL"""
    engine = create_engine(DB_URL)
    return engine

def analyze_file(file_path):
    """Analyze an Excel file"""
    print(f"\n{'='*80}")
    print(f"FILE: {file_path.name}")
    print(f"{'='*80}")
    
    try:
        df = pd.read_excel(file_path)
        print(f"✓ Rows: {len(df):,}")
        print(f"✓ Columns: {len(df.columns)}")
        print(f"\nFirst 5 column names:")
        for i, col in enumerate(df.columns[:5], 1):
            print(f"  {i}. {col}")
        
        # Check for key columns
        key_cols = {
            'Material': ['Material', 'Material Code', 'material'],
            'Quantity': ['Quantity', 'quantity', 'Qty', 'qty_kg'],
            'Date': ['Date', 'Posting Date', 'posting_date', 'Billing Date'],
            'Document': ['Document', 'Material Document', 'Sales Document']
        }
        
        print(f"\nKey column detection:")
        for key, variants in key_cols.items():
            found = [col for col in df.columns if any(v in col for v in variants)]
            if found:
                print(f"  ✓ {key}: {found[0]}")
                # Show sample values
                if len(df) > 0:
                    sample = df[found[0]].head(3).tolist()
                    print(f"    Samples: {sample}")
            else:
                print(f"  ✗ {key}: NOT FOUND")
        
        return {
            'file': file_path.name,
            'rows': len(df),
            'columns': len(df.columns),
            'first_cols': list(df.columns[:5])
        }
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return None

def check_database_counts(engine):
    """Check row counts in database tables"""
    print(f"\n{'='*80}")
    print(f"DATABASE TABLE ROW COUNTS")
    print(f"{'='*80}")
    
    tables = [
        'raw_mb51',
        'raw_zrsd002',
        'raw_zrsd004',
        'raw_zrsd006',
        'raw_zrfi005',
        'raw_cooispi',
        'raw_zrpp062',
        'fact_inventory',
        'fact_billing',
        'fact_delivery',
        'fact_production',
        'fact_production_performance_v2'
    ]
    
    counts = {}
    with engine.connect() as conn:
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                counts[table] = count
                print(f"  {table:40s}: {count:,}")
            except Exception as e:
                print(f"  {table:40s}: ERROR - {e}")
                counts[table] = 0
    
    return counts

def check_sample_data(engine):
    """Sample queries to check data quality"""
    print(f"\n{'='*80}")
    print(f"SAMPLE DATA CHECKS")
    print(f"{'='*80}")
    
    queries = {
        "MB51 Material Count": "SELECT COUNT(DISTINCT material_code) FROM raw_mb51",
        "MB51 Total Qty": "SELECT SUM(CAST(quantity AS NUMERIC)) FROM raw_mb51",
        "ZRSD002 Total Revenue": "SELECT SUM(net_value_in_dc) FROM raw_zrsd002",
        "ZRSD002 Document Count": "SELECT COUNT(DISTINCT billing_document) FROM raw_zrsd002",
        "Fact Inventory Total Qty": "SELECT SUM(qty_kg) FROM fact_inventory",
        "Fact Billing Total Revenue": "SELECT SUM(net_value) FROM fact_billing"
    }
    
    results = {}
    with engine.connect() as conn:
        for name, query in queries.items():
            try:
                result = conn.execute(text(query))
                value = result.scalar()
                results[name] = value
                print(f"  {name:40s}: {value:,.2f}" if value else f"  {name:40s}: NULL")
            except Exception as e:
                print(f"  {name:40s}: ERROR - {e}")
                results[name] = None
    
    return results

def main():
    """Main diagnostic routine"""
    print(f"\n{'#'*80}")
    print(f"# DATA DISCREPANCY DIAGNOSTIC TOOL")
    print(f"{'#'*80}")
    
    # Step 1: Analyze demodata files
    demodata_path = Path("demodata")
    if not demodata_path.exists():
        print(f"✗ ERROR: demodata folder not found at {demodata_path.absolute()}")
        return
    
    excel_files = list(demodata_path.glob("*.XLSX")) + list(demodata_path.glob("*.xlsx"))
    print(f"\nFound {len(excel_files)} Excel files in demodata/")
    
    file_stats = []
    for file_path in sorted(excel_files):
        stats = analyze_file(file_path)
        if stats:
            file_stats.append(stats)
    
    # Step 2: Connect to database and check counts
    print(f"\n{'='*80}")
    print(f"CONNECTING TO DATABASE...")
    print(f"{'='*80}")
    
    try:
        engine = connect_db()
        print(f"✓ Connected to PostgreSQL")
        
        # Check table counts
        db_counts = check_database_counts(engine)
        
        # Check sample data
        sample_results = check_sample_data(engine)
        
    except Exception as e:
        print(f"✗ DATABASE ERROR: {e}")
        return
    
    # Step 3: Summary
    print(f"\n{'='*80}")
    print(f"DIAGNOSTIC SUMMARY")
    print(f"{'='*80}")
    print(f"\n📊 Excel Files Analyzed: {len(file_stats)}")
    for stat in file_stats:
        print(f"  • {stat['file']:30s}: {stat['rows']:,} rows")
    
    print(f"\n🗄️  Database Tables:")
    print(f"  • Raw tables total: {sum(v for k, v in db_counts.items() if k.startswith('raw_')):,} rows")
    print(f"  • Fact tables total: {sum(v for k, v in db_counts.items() if k.startswith('fact_')):,} rows")
    
    print(f"\n⚠️  NEXT STEPS:")
    print(f"  1. Compare Excel row counts with raw table counts")
    print(f"  2. Check if transforms have been run (raw → fact)")
    print(f"  3. Verify dedup/upsert logic is working correctly")
    print(f"  4. Check API aggregation logic")
    
    print(f"\n✓ Diagnostic complete. Review output above for discrepancies.\n")

if __name__ == "__main__":
    main()
