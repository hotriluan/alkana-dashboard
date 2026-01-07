"""
STEP 1: COMPREHENSIVE DATABASE HEALTH CHECK

Audit all tables for:
1. Row counts
2. Duplicates 
3. NULL critical fields
4. Date range validation
5. Comparison with Excel sources
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

BASE_DIR = Path(__file__).parent
DEMODATA_DIR = BASE_DIR / "demodata"

print("="*80)
print("  DATABASE HEALTH CHECK - COMPREHENSIVE AUDIT")
print("="*80)

with engine.connect() as conn:
    
    # ========== PART 1: FACT TABLES AUDIT ==========
    print("\n" + "="*80)
    print("  PART 1: FACT TABLES AUDIT")
    print("="*80)
    
    # fact_billing
    print("\n[1] FACT_BILLING:")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT billing_document || '-' || billing_item) as unique_keys,
            COUNT(*) - COUNT(DISTINCT billing_document || '-' || billing_item) as duplicates,
            MIN(billing_date) as earliest_date,
            MAX(billing_date) as latest_date,
            SUM(net_value)/1000000000 as revenue_billions,
            COUNT(CASE WHEN customer_name IS NULL THEN 1 END) as null_customers
        FROM fact_billing
    """)).fetchone()
    
    print(f"  Total Rows: {result[0]:,}")
    print(f"  Unique Keys: {result[1]:,}")
    print(f"  Duplicates: {result[2]:,} {'<-- ISSUE!' if result[2] > 0 else ''}")
    print(f"  Date Range: {result[3]} to {result[4]}")
    print(f"  Revenue: {result[5]:.2f}B VND")
    print(f"  NULL Customers: {result[6]:,} {'<-- ISSUE!' if result[6] > 0 else ''}")
    
    # Check Excel source
    excel_path = DEMODATA_DIR / "zrsd002.xlsx"
    if excel_path.exists():
        df = pd.read_excel(excel_path)
        excel_rows = len(df)
        diff = result[0] - excel_rows
        print(f"  Excel Source: {excel_rows:,} rows")
        print(f"  Difference: {diff:+,} rows {'<-- ISSUE!' if abs(diff) > excel_rows * 0.01 else ''}")
    
    # fact_production
    print("\n[2] FACT_PRODUCTION:")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT order_number || '-' || COALESCE(batch, '')) as unique_keys,
            COUNT(*) - COUNT(DISTINCT order_number || '-' || COALESCE(batch, '')) as duplicates,
            MIN(start_date) as earliest_date,
            MAX(end_date) as latest_date
        FROM fact_production
    """)).fetchone()
    
    print(f"  Total Rows: {result[0]:,}")
    print(f"  Unique Keys: {result[1]:,}")
    print(f"  Duplicates: {result[2]:,} {'<-- ISSUE!' if result[2] > 0 else ''}")
    print(f"  Date Range: {result[3]} to {result[4]}")
    
    # fact_delivery
    print("\n[3] FACT_DELIVERY:")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            MIN(actual_gi_date) as earliest_date,
            MAX(actual_gi_date) as latest_date
        FROM fact_delivery
    """)).fetchone()
    
    print(f"  Total Rows: {result[0]:,}")
    print(f"  Date Range: {result[1]} to {result[2]}")
    
    # fact_ar_aging
    print("\n[4] FACT_AR_AGING:")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT snapshot_date) as unique_snapshots,
            MIN(snapshot_date) as earliest_snapshot,
            MAX(snapshot_date) as latest_snapshot,
            SUM(CASE WHEN overdue_amount > 0 THEN overdue_amount ELSE 0 END)/1000000000 as overdue_billions
        FROM fact_ar_aging
    """)).fetchone()
    
    print(f"  Total Rows: {result[0]:,}")
    print(f"  Unique Snapshots: {result[1]:,}")
    print(f"  Snapshot Range: {result[2]} to {result[3]}")
    print(f"  Total Overdue: {result[4]:.2f}B VND" if result[4] else "  Total Overdue: N/A")
    
    if result[0] == 0:
        print("  *** WARNING: Table is EMPTY! AR Collection will show nothing ***")
    
    # fact_lead_time
    print("\n[5] FACT_LEAD_TIME:")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT order_number || '-' || COALESCE(batch, '')) as unique_keys,
            COUNT(*) - COUNT(DISTINCT order_number || '-' || COALESCE(batch, '')) as duplicates,
            MIN(start_date) as earliest_date,
            MAX(end_date) as latest_date,
            AVG(lead_time_days) as avg_lead_time
        FROM fact_lead_time
    """)).fetchone()
    
    print(f"  Total Rows: {result[0]:,}")
    print(f"  Unique Keys: {result[1]:,}")
    print(f"  Duplicates: {result[2]:,} {'<-- ISSUE!' if result[2] > 0 else ''}")
    print(f"  Date Range: {result[3]} to {result[4]}")
    print(f"  Avg Lead Time: {result[5]:.1f} days" if result[5] else "  Avg Lead Time: N/A")
    
    # fact_alerts
    print("\n[6] FACT_ALERTS:")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            MIN(detected_at) as earliest_alert,
            MAX(detected_at) as latest_alert,
            COUNT(DISTINCT alert_type) as alert_types
        FROM fact_alerts
    """)).fetchone()
    
    print(f"  Total Rows: {result[0]:,}")
    print(f"  Alert Types: {result[1]:,}")
    print(f"  Date Range: {result[2]} to {result[3]}")
    
    # ========== PART 2: RAW TABLES AUDIT ==========
    print("\n" + "="*80)
    print("  PART 2: RAW TABLES AUDIT")
    print("="*80)
    
    raw_tables = {
        'raw_cooispi': 'cooispi.XLSX',
        'raw_mb51': 'mb51.XLSX',
        'raw_zrmm024': 'zrmm024.XLSX',
        'raw_zrsd002': 'zrsd002.xlsx',
        'raw_zrsd004': 'zrsd004.XLSX',
        'raw_zrsd006': 'zrsd006.XLSX',
        'raw_zrfi005': 'ZRFI005.XLSX',
    }
    
    for table, excel_file in raw_tables.items():
        db_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        
        excel_path = DEMODATA_DIR / excel_file
        if excel_path.exists():
            df = pd.read_excel(excel_path)
            excel_count = len(df)
            diff = db_count - excel_count
            diff_pct = (diff / excel_count * 100) if excel_count > 0 else 0
            
            status = ""
            if db_count == 0:
                status = "<-- EMPTY!"
            elif abs(diff_pct) > 1:
                status = f"<-- MISMATCH ({diff_pct:+.1f}%)"
            
            print(f"\n{table}:")
            print(f"  DB: {db_count:,} rows")
            print(f"  Excel: {excel_count:,} rows")
            print(f"  Diff: {diff:+,} rows {status}")
        else:
            print(f"\n{table}:")
            print(f"  DB: {db_count:,} rows")
            print(f"  Excel: File not found")
    
    # ========== PART 3: CRITICAL ISSUES SUMMARY ==========
    print("\n" + "="*80)
    print("  CRITICAL ISSUES SUMMARY")
    print("="*80)
    
    issues = []
    
    # Check fact_billing duplicates
    dup_count = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT billing_document || '-' || billing_item)
        FROM fact_billing
    """)).scalar()
    if dup_count > 0:
        issues.append(f"fact_billing has {dup_count:,} duplicate rows")
    
    # Check fact_ar_aging empty
    ar_count = conn.execute(text("SELECT COUNT(*) FROM fact_ar_aging")).scalar()
    if ar_count == 0:
        issues.append("fact_ar_aging is EMPTY - AR Collection will not work")
    
    # Check raw tables empty
    for table in raw_tables.keys():
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        if count == 0:
            issues.append(f"{table} is EMPTY - needs re-load")
    
    if issues:
        print("\nFOUND ISSUES:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\nNo critical issues found!")
    
    print("\n" + "="*80)
    print("  AUDIT COMPLETE")
    print("="*80)
