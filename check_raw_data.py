"""
Check raw_zrsd002 data to see if full data was loaded
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alkana_db")
engine = create_engine(DATABASE_URL)

print("Checking raw_zrsd002 data...\n")

with engine.connect() as conn:
    # Check raw data
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT raw_data->>'Billing Document') as unique_docs,
            MIN((raw_data->>'Billing Date')::date) as min_date,
            MAX((raw_data->>'Billing Date')::date) as max_date
        FROM raw_zrsd002
        WHERE raw_data->>'Billing Date' IS NOT NULL
    """))
    row = result.fetchone()
    
    print(f"Raw zrsd002 table:")
    print(f"  Total rows: {row[0]}")
    print(f"  Unique documents: {row[1]}")
    print(f"  Date range: {row[2]} to {row[3]}")
    
    # Check by month
    print(f"\nData by month in raw_zrsd002:")
    result2 = conn.execute(text("""
        SELECT 
            TO_CHAR((raw_data->>'Billing Date')::date, 'YYYY-MM') as month,
            COUNT(*) as row_count,
            COUNT(DISTINCT raw_data->>'Billing Document') as doc_count
        FROM raw_zrsd002
        WHERE raw_data->>'Billing Date' IS NOT NULL
        GROUP BY month
        ORDER BY month
    """))
    
    for row in result2:
        print(f"  {row[0]}: {row[1]} rows, {row[2]} docs")
    
    # Check fact_billing by month
    print(f"\nData by month in fact_billing:")
    result3 = conn.execute(text("""
        SELECT 
            TO_CHAR(billing_date, 'YYYY-MM') as month,
            COUNT(*) as row_count,
            COUNT(DISTINCT billing_document) as doc_count
        FROM fact_billing
        GROUP BY month
        ORDER BY month
    """))
    
    for row in result3:
        print(f"  {row[0]}: {row[1]} rows, {row[2]} docs")
