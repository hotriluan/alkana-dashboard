from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Check fact_billing
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT billing_document) as unique_docs,
            SUM(net_value)/1000000000 as revenue_billions
        FROM fact_billing
    """)).fetchone()
    
    print(f"\n✅ FACT_BILLING STATUS:")
    print(f"  Total rows: {result[0]:,}")
    print(f"  Unique documents: {result[1]:,}")
    print(f"  Revenue: {result[2]:.2f}B VND")
    
    # Check for duplicates
    dups = conn.execute(text("""
        SELECT billing_document, billing_item, COUNT(*) as cnt
        FROM fact_billing
        GROUP BY billing_document, billing_item
        HAVING COUNT(*) > 1
        LIMIT 5
    """)).fetchall()
    
    if dups:
        print(f"\n⚠️ DUPLICATES FOUND in fact_billing:")
        for dup in dups:
            print(f"  - Doc {dup[0]}, Item {dup[1]}: {dup[2]} times")
    else:
        print(f"\n✅ No duplicates in fact_billing")
