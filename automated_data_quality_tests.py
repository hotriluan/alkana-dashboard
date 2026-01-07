"""
Automated Data Quality Tests

Run this after every data load to ensure quality
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

BASE_DIR = Path(__file__).parent
DEMODATA_DIR = BASE_DIR / "demodata"

def test_no_duplicates():
    """Test: No duplicates in raw tables"""
    print("\n🔍 TEST: Checking for duplicates in raw tables...")
    
    tests = [
        {
            'table': 'raw_zrsd002',
            'keys': "(raw_data->>'Billing Document', raw_data->>'Billing Item')"
        },
        {
            'table': 'raw_mb51',
            'keys': "(raw_data->>'Material Document', raw_data->>'Material Doc.Item')"
        },
        {
            'table': 'raw_cooispi',
            'keys': "(raw_data->>'Order', raw_data->>'Material')"
        },
    ]
    
    passed = True
    with engine.connect() as conn:
        for test in tests:
            result = conn.execute(text(f"""
                SELECT COUNT(*) - COUNT(DISTINCT {test['keys']}) as dups
                FROM {test['table']}
                WHERE {test['keys'].split(',')[0].strip()} IS NOT NULL
            """)).scalar()
            
            if result > 0:
                print(f"  ✗ {test['table']}: {result} duplicates found!")
                passed = False
            else:
                print(f"  ✓ {test['table']}: No duplicates")
    
    return passed

def test_row_counts_match_excel():
    """Test: Database row counts match Excel files"""
    print("\n🔍 TEST: Validating row counts against Excel...")
    
    files = {
        'zrsd002.xlsx': 'raw_zrsd002',
        'mb51.XLSX': 'raw_mb51',
        'cooispi.XLSX': 'raw_cooispi',
    }
    
    passed = True
    with engine.connect() as conn:
        for filename, table in files.items():
            excel_path = DEMODATA_DIR / filename
            if not excel_path.exists():
                continue
            
            df = pd.read_excel(excel_path)
            excel_count = len(df)
            
            db_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            
            diff_pct = abs(excel_count - db_count) / excel_count * 100 if excel_count > 0 else 0
            
            if diff_pct > 1:
                print(f"  ✗ {table}: Excel {excel_count:,} vs DB {db_count:,} ({diff_pct:.1f}% diff)")
                passed = False
            else:
                print(f"  ✓ {table}: {db_count:,} rows match Excel")
    
    return passed

def test_fact_billing_integrity():
    """Test: fact_billing has correct data"""
    print("\n🔍 TEST: Checking fact_billing integrity...")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT billing_document) as unique_docs,
                COUNT(CASE WHEN customer_name IS NULL THEN 1 END) as null_customers,
                SUM(net_value)/1000000000 as revenue_b
            FROM fact_billing
        """)).fetchone()
        
        passed = True
        
        # Should have data
        if result[0] == 0:
            print(f"  ✗ No data in fact_billing!")
            passed = False
        else:
            print(f"  ✓ Total rows: {result[0]:,}")
        
        # Should have customers
        if result[2] > 0:
            null_pct = result[2] / result[0] * 100
            print(f"  ✗ {result[2]:,} rows ({null_pct:.1f}%) have NULL customer_name!")
            passed = False
        else:
            print(f"  ✓ All rows have customer names")
        
        # Revenue should be reasonable
        if result[3] < 100 or result[3] > 1000:
            print(f"  ⚠ Revenue {result[3]:.2f}B seems unusual")
        else:
            print(f"  ✓ Revenue: {result[3]:.2f}B VND")
        
        return passed

def run_all_tests():
    """Run all data quality tests"""
    print("="*80)
    print("  AUTOMATED DATA QUALITY TESTS")
    print("="*80)
    
    results = {
        'No Duplicates': test_no_duplicates(),
        'Row Counts Match Excel': test_row_counts_match_excel(),
        'Fact Billing Integrity': test_fact_billing_integrity(),
    }
    
    print("\n" + "="*80)
    print("  TEST RESULTS SUMMARY")
    print("="*80)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️ SOME TESTS FAILED - Please review!")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
