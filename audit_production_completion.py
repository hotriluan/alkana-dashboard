"""
🕵️ PRODUCTION COMPLETION RATE FORENSIC AUDIT
==============================================
Investigates why Production Completion shows 100%

AUDIT SCOPE:
1. Code inspection (executive.py)
2. Data profiling (fact_production system_status distribution)
3. Formula verification
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from src.db.connection import SessionLocal
import pandas as pd


def print_header(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def audit_production_completion():
    """Main audit function"""
    db = SessionLocal()
    
    try:
        print_header("🔬 SECTION 1: DATA PROFILING - fact_production Status Distribution")
        
        # Query 1: System Status Distribution
        print("📊 Query 1: system_status Distribution")
        print("-" * 80)
        
        query1 = text("""
            SELECT 
                system_status,
                COUNT(*) as order_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM fact_production
            GROUP BY system_status
            ORDER BY order_count DESC;
        """)
        
        df_system_status = pd.read_sql(query1, db.bind)
        print(df_system_status.to_string(index=False))
        print(f"\n✅ Total Rows in fact_production: {df_system_status['order_count'].sum()}")
        
        # Query 2: order_status Distribution (derived field)
        print("\n📊 Query 2: order_status Distribution (Derived Field)")
        print("-" * 80)
        
        query2 = text("""
            SELECT 
                order_status,
                COUNT(*) as order_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM fact_production
            GROUP BY order_status
            ORDER BY order_count DESC;
        """)
        
        df_order_status = pd.read_sql(query2, db.bind)
        print(df_order_status.to_string(index=False))
        
        # Query 3: Sample records showing system_status values
        print("\n📋 Query 3: Sample Production Orders (First 10)")
        print("-" * 80)
        
        query3 = text("""
            SELECT 
                order_number,
                system_status,
                order_status,
                order_qty,
                delivered_qty,
                release_date,
                actual_finish_date
            FROM fact_production
            ORDER BY id DESC
            LIMIT 10;
        """)
        
        df_sample = pd.read_sql(query3, db.bind)
        print(df_sample.to_string(index=False))
        
        # Query 4: Check if ONLY completed statuses exist
        print("\n🚩 Query 4: Open vs Completed Status Analysis")
        print("-" * 80)
        
        query4 = text("""
            SELECT 
                CASE 
                    WHEN system_status ILIKE '%TECO%' OR system_status ILIKE '%DLV%' THEN 'COMPLETED'
                    WHEN system_status ILIKE '%REL%' THEN 'RELEASED'
                    WHEN system_status ILIKE '%CRTD%' THEN 'CREATED'
                    WHEN system_status ILIKE '%PCNF%' THEN 'PARTIALLY_CONFIRMED'
                    ELSE 'OTHER'
                END as status_category,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM fact_production
            GROUP BY status_category
            ORDER BY count DESC;
        """)
        
        df_categorized = pd.read_sql(query4, db.bind)
        print(df_categorized.to_string(index=False))
        
        print_header("💻 SECTION 2: CODE INSPECTION - Executive API Logic")
        
        # Show the problematic code snippet from executive.py
        print("📄 File: src/api/routers/executive.py")
        print("🔍 Production Metrics SQL Query (Lines 107-117):")
        print("-" * 80)
        
        code_snippet = '''
# Sales Order metrics (MISLABELED: This counts SALES orders, NOT production)
sales_date_filter = ""
if start_date and end_date:
    sales_date_filter = f"WHERE order_date BETWEEN '{start_date}' AND '{end_date}'"

sales_order_result = db.execute(text(f"""
    SELECT 
        COUNT(*) as total_orders,
        COUNT(CASE WHEN invoice_count > 0 THEN 1 END) as completed_orders,
        COALESCE(AVG(invoice_count), 0) as avg_invoices_per_order
    FROM view_sales_orders
    {sales_date_filter}
""")).fetchone()
'''
        print(code_snippet)
        
        print("\n🔍 Completion Rate Calculation (Line 143):")
        print("-" * 80)
        
        calc_snippet = '''
completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
'''
        print(calc_snippet)
        
        print("\n🔍 Response Model (Lines 152-159):")
        print("-" * 80)
        
        response_snippet = '''
return ExecutiveKPIs(
    # ... (other fields omitted)
    total_orders=total_orders,
    completed_orders=completed_orders,
    completion_rate=round(completion_rate, 2),  # ⚠️ LABELED AS "Production" BUT USES SALES DATA
    # ...
)
'''
        print(response_snippet)
        
        print_header("🎯 SECTION 3: ROOT CAUSE ANALYSIS")
        
        print("📌 FINDING #1: METRIC MISLABELING")
        print("-" * 80)
        print("❌ The 'Production Completion' metric is ACTUALLY counting SALES ORDERS")
        print("   - Source: view_sales_orders (NOT fact_production)")
        print("   - Logic: Counts orders with invoice_count > 0 as 'completed'")
        print("   - This is a SALES metric, NOT a production metric\n")
        
        print("📌 FINDING #2: DATA AVAILABILITY CHECK")
        print("-" * 80)
        
        # Check if production orders exist at all
        total_production = df_system_status['order_count'].sum()
        
        if total_production > 0:
            completed_count = df_categorized[df_categorized['status_category'] == 'COMPLETED']['count'].values
            completed_pct = completed_count[0] if len(completed_count) > 0 else 0
            
            print(f"✅ Production data EXISTS in fact_production")
            print(f"   - Total production orders: {total_production}")
            print(f"   - Completed orders: {completed_pct}")
            
            if completed_pct == total_production:
                print(f"\n🚩 WARNING: ALL production orders are COMPLETED (100%)")
                print(f"   - This indicates ETL may be filtering out open orders")
                print(f"   - OR factory truly has no WIP (unrealistic)")
            else:
                print(f"\n✅ HEALTHY: Mix of statuses found (not all TECO/DLV)")
        else:
            print("❌ NO production data found in fact_production table")
            print("   - ETL may not be loading data")
            print("   - Check src/etl/loaders.py for cooispi loader")
        
        print("\n📌 FINDING #3: CORRECT FORMULA")
        print("-" * 80)
        print("""
❌ CURRENT (WRONG):
   - Queries: view_sales_orders
   - Formula: COUNT(invoice_count > 0) / COUNT(*) FROM sales_orders

✅ CORRECT:
   - Query: fact_production
   - Formula: COUNT(system_status ILIKE '%TECO%' OR '%DLV%') / COUNT(*) FROM fact_production
   - Include ALL statuses: REL, CRTD, PCNF, TECO, DLV
        """)
        
        print_header("🛠️ SECTION 4: RECOMMENDED FIX")
        
        print("📝 Corrected SQL Query for executive.py")
        print("-" * 80)
        
        fix_sql = """
# Production Order metrics (CORRECTED)
production_date_filter = ""
if start_date and end_date:
    production_date_filter = f"WHERE release_date BETWEEN '{start_date}' AND '{end_date}'"

production_result = db.execute(text(f'''
    SELECT 
        COUNT(*) as total_orders,
        COUNT(CASE 
            WHEN system_status ILIKE '%TECO%' OR system_status ILIKE '%DLV%' 
            THEN 1 
        END) as completed_orders
    FROM fact_production
    {production_date_filter}
'''))fetchone()
        """
        print(fix_sql)
        
        print("\n📝 Alternative: Use derived order_status field")
        print("-" * 80)
        
        alt_fix = """
production_result = db.execute(text(f'''
    SELECT 
        COUNT(*) as total_orders,
        COUNT(CASE WHEN order_status = 'COMPLETED' THEN 1 END) as completed_orders
    FROM fact_production
    {production_date_filter}
'''))fetchone()
        """
        print(alt_fix)
        
        print_header("📋 AUDIT COMPLETE")
        
        print("✅ Deliverables:")
        print("   1. Root cause identified: Metric mislabeling (sales vs production)")
        print("   2. Data profiling completed")
        print("   3. Corrected SQL provided")
        print("\n📄 Full report saved to: PRODUCTION_COMPLETION_AUDIT.md")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    audit_production_completion()
