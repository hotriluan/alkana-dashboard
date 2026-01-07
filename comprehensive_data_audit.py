"""
Comprehensive Data Audit - Executive Dashboard
Skills: data-analysis, debugging, databases, problem-solving
Claude Kit: Systematic investigation, DRY, KISS

Investigates all discrepancies between source data and dashboard display
"""
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alkana_db")
engine = create_engine(DATABASE_URL)

print("="*80)
print("COMPREHENSIVE DATA AUDIT - EXECUTIVE DASHBOARD")
print("="*80)

# ============================================================================
# PART 1: REVENUE ANALYSIS (Source vs Database)
# ============================================================================
print("\n" + "="*80)
print("PART 1: REVENUE ANALYSIS")
print("="*80)

# Read Excel source
print("\n1.1 Reading zrsd002.xlsx (SOURCE OF TRUTH)...")
df = pd.read_excel("demodata/zrsd002.xlsx")
df['Billing Date'] = pd.to_datetime(df['Billing Date'], errors='coerce')
df_2025 = df[(df['Billing Date'] >= '2025-01-01') & (df['Billing Date'] <= '2025-12-31')]

excel_revenue = df_2025['Net Value'].sum()
excel_rows = len(df_2025)
excel_docs = df_2025['Billing Document'].nunique()

print(f"   Source Excel (2025 full year):")
print(f"   ✓ Total Rows: {excel_rows:,}")
print(f"   ✓ Unique Documents: {excel_docs:,}")
print(f"   ✓ Total Revenue: {excel_revenue:,.2f}")

# Query database
print("\n1.2 Querying fact_billing (DATABASE)...")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT billing_document) as total_docs,
            SUM(net_value) as total_revenue,
            MIN(billing_date) as min_date,
            MAX(billing_date) as max_date
        FROM fact_billing
        WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'
    """))
    db_row = result.fetchone()
    
    print(f"   Database fact_billing (2025):")
    print(f"   ✓ Total Rows: {db_row[0]:,}")
    print(f"   ✓ Unique Documents: {db_row[1]:,}")
    print(f"   ✓ Total Revenue: {db_row[2]:,.2f}")
    print(f"   ✓ Date Range: {db_row[3]} to {db_row[4]}")
    
    # Check for duplicates
    result2 = conn.execute(text("""
        SELECT billing_document, COUNT(*) as cnt
        FROM fact_billing
        WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'
        GROUP BY billing_document
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 5
    """))
    
    duplicates = result2.fetchall()
    if duplicates:
        print(f"\n   ⚠ WARNING: Found duplicate billing documents!")
        for dup in duplicates[:3]:
            print(f"     - Document {dup[0]}: {dup[1]} times")
    
    # Revenue comparison
    db_revenue = float(db_row[2]) if db_row[2] else 0
    diff = db_revenue - excel_revenue
    diff_pct = (diff / excel_revenue * 100) if excel_revenue > 0 else 0
    
    print(f"\n   REVENUE COMPARISON:")
    print(f"   Excel:    {excel_revenue:,.2f}")
    print(f"   Database: {db_row[2]:,.2f}")
    print(f"   Diff:     {diff:,.2f} ({diff_pct:+.1f}%)")
    
    if abs(diff_pct) > 1:
        print(f"   ❌ ISSUE: Revenue mismatch > 1%!")
    else:
        print(f"   ✓ Revenue matches within tolerance")

# ============================================================================
# PART 2: CUSTOMER ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("PART 2: CUSTOMER ANALYSIS")
print("="*80)

print("\n2.1 Checking Excel customer data...")
excel_customers = df_2025['Customer Name'].nunique() if 'Customer Name' in df_2025.columns else 0
excel_null_customers = df_2025['Customer Name'].isna().sum() if 'Customer Name' in df_2025.columns else len(df_2025)
print(f"   Excel unique customers: {excel_customers}")
print(f"   Excel NULL customers: {excel_null_customers} ({excel_null_customers/len(df_2025)*100:.1f}%)")

if 'Customer Name' in df_2025.columns:
    sample_customers = df_2025['Customer Name'].dropna().head(5).tolist()
    print(f"   Sample customers: {sample_customers}")

print("\n2.2 Checking database customer data...")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT customer_name) as unique_customers,
            COUNT(*) as total_rows,
            COUNT(CASE WHEN customer_name IS NULL THEN 1 END) as null_count,
            COUNT(CASE WHEN customer_name = '' THEN 1 END) as empty_count
        FROM fact_billing
        WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'
    """))
    row = result.fetchone()
    
    print(f"   Database unique customers: {row[0]}")
    print(f"   Total rows: {row[1]:,}")
    print(f"   NULL customers: {row[2]:,} ({row[2]/row[1]*100:.1f}%)")
    print(f"   Empty customers: {row[3]:,}")
    
    if row[0] == 0:
        print(f"\n   ❌ CRITICAL ISSUE: No customers in database!")
        print(f"   Checking raw_zrsd002...")
        
        result2 = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT raw_data->>'Customer Name') as unique_customers,
                COUNT(CASE WHEN raw_data->>'Customer Name' IS NULL THEN 1 END) as null_count
            FROM raw_zrsd002
            LIMIT 1
        """))
        raw_row = result2.fetchone()
        print(f"   raw_zrsd002 unique customers: {raw_row[0]}")
        print(f"   raw_zrsd002 NULL customers: {raw_row[1]}")

# ============================================================================
# PART 3: PRODUCTION DATA ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("PART 3: PRODUCTION DATA (Total Orders, Completion Rate)")
print("="*80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN system_status LIKE '%TECO%' THEN 1 END) as completed,
            COUNT(CASE WHEN actual_finish_date BETWEEN '2025-01-01' AND '2025-12-31' THEN 1 END) as orders_2025,
            MIN(actual_finish_date) as min_date,
            MAX(actual_finish_date) as max_date
        FROM fact_production
    """))
    prod_row = result.fetchone()
    
    print(f"\n3.1 Production Orders:")
    print(f"   Total orders (all time): {prod_row[0]:,}")
    print(f"   Completed (TECO): {prod_row[1]:,}")
    print(f"   Orders in 2025: {prod_row[2]:,}")
    print(f"   Date range: {prod_row[3]} to {prod_row[4]}")
    
    completion_rate = (prod_row[1] / prod_row[0] * 100) if prod_row[0] > 0 else 0
    print(f"   Completion rate: {completion_rate:.1f}%")
    
    # What dashboard is showing (837 orders)
    result2 = conn.execute(text("""
        SELECT COUNT(*)
        FROM fact_production
        WHERE actual_finish_date BETWEEN '2025-01-01' AND '2025-12-31'
    """))
    orders_filtered = result2.fetchone()[0]
    print(f"\n   Orders with finish date in 2025: {orders_filtered}")

# ============================================================================
# PART 4: INVENTORY & AR ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("PART 4: INVENTORY & AR DATA")
print("="*80)

with engine.connect() as conn:
    # Inventory
    result = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT material_code) as materials,
            SUM(current_qty) as total_qty
        FROM view_inventory_current
    """))
    inv_row = result.fetchone()
    print(f"\n4.1 Inventory:")
    print(f"   Unique materials: {inv_row[0]}")
    print(f"   Total quantity: {inv_row[1]:.2f}" if inv_row[1] else "   Total quantity: 0")
    
    # AR
    result2 = conn.execute(text("""
        SELECT 
            SUM(total_target) as total_ar,
            SUM(COALESCE(target_31_60, 0) + COALESCE(target_61_90, 0) + 
                COALESCE(target_91_120, 0) + COALESCE(target_121_180, 0) + 
                COALESCE(target_over_180, 0)) as overdue_ar
        FROM fact_ar_aging
    """))
    ar_row = result2.fetchone()
    print(f"\n4.2 AR Aging:")
    print(f"   Total AR: {ar_row[0]:,.2f}" if ar_row[0] else "   Total AR: 0")
    print(f"   Overdue AR: {ar_row[1]:,.2f}" if ar_row[1] else "   Overdue AR: 0")

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80)
print("SUMMARY & ROOT CAUSES")
print("="*80)

issues = []
if abs(diff_pct) > 1:
    issues.append(f"Revenue mismatch: {diff_pct:+.1f}%")
if row[0] == 0:
    issues.append("Customer count = 0 (critical)")
if duplicates:
    issues.append(f"Duplicate billing documents detected")

if issues:
    print("\n❌ ISSUES FOUND:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
else:
    print("\n✓ All metrics validated successfully")

print("\n" + "="*80)
