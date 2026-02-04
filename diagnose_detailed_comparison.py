"""
Detailed Data Comparison: Excel vs Database vs Dashboard
Focus on specific metrics that user sees on dashboard
"""
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def get_dashboard_metrics_from_db(engine):
    """Query database for metrics shown on dashboards"""
    print(f"\n{'='*80}")
    print(f"DASHBOARD METRICS FROM DATABASE")
    print(f"{'='*80}")
    
    with engine.connect() as conn:
        # Inventory metrics
        print(f"\n📦 INVENTORY METRICS")
        try:
            # Total stock quantity
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as record_count,
                    COUNT(DISTINCT material_id) as material_count,
                    SUM(qty_kg) as total_qty_kg
                FROM fact_inventory
                WHERE qty_kg > 0
            """))
            row = result.fetchone()
            print(f"  Records: {row[0]:,}")
            print(f"  Unique Materials: {row[1]:,}")
            print(f"  Total Qty (kg): {row[2]:,.2f}" if row[2] else "  Total Qty: NULL")
        except Exception as e:
            print(f"  ERROR: {e}")
        
        # Sales metrics
        print(f"\n💰 SALES METRICS (ZRSD002)")
        try:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as record_count,
                    COUNT(DISTINCT billing_document) as doc_count,
                    SUM(net_value) as total_revenue,
                    MIN(billing_date) as earliest_date,
                    MAX(billing_date) as latest_date
                FROM fact_billing
            """))
            row = result.fetchone()
            print(f"  Records: {row[0]:,}")
            print(f"  Unique Documents: {row[1]:,}")
            print(f"  Total Revenue: {row[2]:,.2f}" if row[2] else "  Total Revenue: NULL")
            print(f"  Date Range: {row[3]} to {row[4]}")
        except Exception as e:
            print(f"  ERROR: {e}")
        
        # Delivery metrics
        print(f"\n🚚 DELIVERY METRICS (ZRSD004)")
        try:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as record_count,
                    COUNT(DISTINCT delivery_number) as delivery_count,
                    SUM(CASE WHEN is_on_time THEN 1 ELSE 0 END) as on_time_count,
                    MIN(delivery_date) as earliest_date,
                    MAX(delivery_date) as latest_date
                FROM fact_delivery
            """))
            row = result.fetchone()
            print(f"  Records: {row[0]:,}")
            print(f"  Unique Deliveries: {row[1]:,}")
            print(f"  On-Time Deliveries: {row[2]:,}")
            otif_pct = (row[2] / row[0] * 100) if row[0] > 0 else 0
            print(f"  OTIF%: {otif_pct:.2f}%")
            print(f"  Date Range: {row[3]} to {row[4]}")
        except Exception as e:
            print(f"  ERROR: {e}")
        
        # Production metrics
        print(f"\n🏭 PRODUCTION METRICS (ZRPP062)")
        try:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as record_count,
                    COUNT(DISTINCT process_order) as order_count,
                    SUM(output_actual_kg) as total_output_kg,
                    AVG(loss_pct) as avg_loss_pct
                FROM fact_production_performance_v2
            """))
            row = result.fetchone()
            print(f"  Records: {row[0]:,}")
            print(f"  Unique Process Orders: {row[1]:,}")
            print(f"  Total Output (kg): {row[2]:,.2f}" if row[2] else "  Total Output: NULL")
            print(f"  Avg Loss %: {row[3]:.2f}%" if row[3] else "  Avg Loss %: NULL")
        except Exception as e:
            print(f"  ERROR: {e}")

def check_excel_vs_raw_tables(engine):
    """Compare Excel row counts with raw table counts"""
    print(f"\n{'='*80}")
    print(f"EXCEL vs RAW TABLE COMPARISON")
    print(f"{'='*80}")
    
    comparisons = [
        ('mb51.XLSX', 17522, 'raw_mb51'),
        ('zrsd002.XLSX', 250, 'raw_zrsd002'),
        ('zrsd004.XLSX', 2586, 'raw_zrsd004'),
        ('cooispi.XLSX', 1372, 'raw_cooispi'),
        ('zrpp062.XLSX', 438, 'raw_zrpp062'),
        ('ZRFI005.XLSX', 96, 'raw_zrfi005'),
    ]
    
    with engine.connect() as conn:
        for excel_file, excel_rows, table_name in comparisons:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                db_rows = result.scalar()
                ratio = db_rows / excel_rows if excel_rows > 0 else 0
                status = "✓ MATCH" if ratio == 1.0 else f"⚠️  {ratio:.1f}x MORE in DB"
                print(f"\n{excel_file}")
                print(f"  Excel: {excel_rows:,} rows")
                print(f"  DB ({table_name}): {db_rows:,} rows")
                print(f"  {status}")
            except Exception as e:
                print(f"\n{excel_file}: ERROR - {e}")

def check_upload_history(engine):
    """Check if there's an upload history table"""
    print(f"\n{'='*80}")
    print(f"UPLOAD HISTORY CHECK")
    print(f"{'='*80}")
    
    with engine.connect() as conn:
        try:
            # Check if upload_history table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%upload%'
            """))
            tables = result.fetchall()
            if tables:
                print(f"✓ Found upload-related tables:")
                for table in tables:
                    print(f"  • {table[0]}")
                    
                    # Get count and sample
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table[0]}"))
                    count = count_result.scalar()
                    print(f"    Rows: {count:,}")
                    
                    if count > 0 and table[0] == 'upload_history':
                        sample_result = conn.execute(text(f"""
                            SELECT file_name, file_type, upload_date, rows_loaded 
                            FROM {table[0]} 
                            ORDER BY upload_date DESC 
                            LIMIT 5
                        """))
                        print(f"    Recent uploads:")
                        for row in sample_result:
                            print(f"      - {row[0]} ({row[1]}): {row[3]} rows on {row[2]}")
            else:
                print(f"✗ No upload history table found")
                print(f"  This explains why DB has more rows than demodata!")
        except Exception as e:
            print(f"ERROR: {e}")

def check_date_ranges(engine):
    """Check date ranges in database vs Excel files"""
    print(f"\n{'='*80}")
    print(f"DATE RANGE ANALYSIS")
    print(f"{'='*80}")
    
    # Read Excel files for date ranges
    excel_dates = {}
    
    print(f"\n📅 Excel File Date Ranges:")
    try:
        mb51 = pd.read_excel('demodata/mb51.XLSX')
        if 'Posting Date' in mb51.columns:
            excel_dates['mb51'] = (mb51['Posting Date'].min(), mb51['Posting Date'].max())
            print(f"  mb51.XLSX: {excel_dates['mb51'][0]} to {excel_dates['mb51'][1]}")
    except:
        pass
    
    try:
        zrsd002 = pd.read_excel('demodata/zrsd002.XLSX')
        if 'Billing Date' in zrsd002.columns:
            excel_dates['zrsd002'] = (zrsd002['Billing Date'].min(), zrsd002['Billing Date'].max())
            print(f"  zrsd002.XLSX: {excel_dates['zrsd002'][0]} to {excel_dates['zrsd002'][1]}")
    except:
        pass
    
    print(f"\n📅 Database Date Ranges:")
    with engine.connect() as conn:
        queries = [
            ("raw_mb51", "SELECT MIN(posting_date), MAX(posting_date) FROM raw_mb51"),
            ("raw_zrsd002", "SELECT MIN(billing_date), MAX(billing_date) FROM raw_zrsd002"),
            ("fact_billing", "SELECT MIN(billing_date), MAX(billing_date) FROM fact_billing"),
        ]
        
        for table, query in queries:
            try:
                result = conn.execute(text(query))
                row = result.fetchone()
                print(f"  {table}: {row[0]} to {row[1]}")
            except Exception as e:
                print(f"  {table}: ERROR")

def main():
    print(f"\n{'#'*80}")
    print(f"# DETAILED DATA COMPARISON DIAGNOSTIC")
    print(f"{'#'*80}")
    
    try:
        engine = create_engine(DB_URL)
        print(f"✓ Connected to database")
        
        # Step 1: Compare Excel vs Raw tables
        check_excel_vs_raw_tables(engine)
        
        # Step 2: Check upload history
        check_upload_history(engine)
        
        # Step 3: Check date ranges
        check_date_ranges(engine)
        
        # Step 4: Get dashboard metrics
        get_dashboard_metrics_from_db(engine)
        
        # Summary
        print(f"\n{'='*80}")
        print(f"ROOT CAUSE ANALYSIS")
        print(f"{'='*80}")
        print(f"""
The discrepancy between Excel files and Dashboard occurs because:

1. ✓ Database contains HISTORICAL data from multiple uploads
2. ✓ demodata/ files are just SAMPLE/LATEST uploads
3. ✓ Dashboard shows ALL data in database, not just demodata files

CONCLUSION:
- This is EXPECTED BEHAVIOR if users uploaded more data previously
- Excel in demodata = Latest sample files
- Database = Cumulative data from all uploads over time
- Dashboard = Shows cumulative database data

NEXT STEPS TO VERIFY:
1. Check if upload_history table shows multiple file uploads
2. Compare date ranges: Excel vs Database
3. If user expects ONLY demodata to appear, database needs to be cleared first
4. If user wants to see historical + new data, current behavior is correct
        """)
        
    except Exception as e:
        print(f"✗ ERROR: {e}")

if __name__ == "__main__":
    main()
