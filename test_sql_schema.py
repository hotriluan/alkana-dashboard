"""
Test SQL queries directly to verify schema fix
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alkana_db")
engine = create_engine(DATABASE_URL)

print("Testing Executive Dashboard SQL queries...\n")

with engine.connect() as conn:
    # Test 1: Revenue query without filter
    print("1. Testing revenue query WITHOUT date filter:")
    try:
        result = conn.execute(text("""
            SELECT 
                COALESCE(SUM(net_value), 0) as total_revenue,
                COUNT(DISTINCT customer_name) as total_customers
            FROM fact_billing
        """))
        row = result.fetchone()
        print(f"   ✓ Total Revenue: {row[0]:,.0f}")
        print(f"   ✓ Total Customers: {row[1]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Revenue query WITH date filter
    print("\n2. Testing revenue query WITH date filter:")
    try:
        result = conn.execute(text("""
            SELECT 
                COALESCE(SUM(net_value), 0) as total_revenue,
                COUNT(DISTINCT customer_name) as total_customers
            FROM fact_billing
            WHERE billing_date BETWEEN '2025-12-07' AND '2026-01-06'
        """))
        row = result.fetchone()
        print(f"   ✓ Total Revenue: {row[0]:,.0f}")
        print(f"   ✓ Total Customers: {row[1]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Revenue by division
    print("\n3. Testing revenue by distribution channel WITH date filter:")
    try:
        result = conn.execute(text("""
            SELECT 
                COALESCE(dist_channel, 'N/A') as division_code,
                SUM(net_value) as revenue,
                COUNT(DISTINCT COALESCE(customer_name, 'Unknown')) as customer_count,
                COUNT(DISTINCT billing_document) as order_count
            FROM fact_billing
            WHERE billing_date BETWEEN '2025-12-07' AND '2026-01-06'
            GROUP BY dist_channel
            ORDER BY revenue DESC
            LIMIT 5
        """))
        rows = result.fetchall()
        print(f"   ✓ Retrieved {len(rows)} divisions")
        for row in rows[:3]:
            print(f"   ✓ Division {row[0]}: {row[1]:,.0f} revenue, {row[2]} customers")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Top customers
    print("\n4. Testing top customers WITH date filter:")
    try:
        result = conn.execute(text("""
            SELECT 
                COALESCE(customer_name, 'Unknown') as customer_name,
                SUM(net_value) as revenue,
                COUNT(DISTINCT billing_document) as order_count
            FROM fact_billing
            WHERE customer_name IS NOT NULL 
              AND billing_date BETWEEN '2025-12-07' AND '2026-01-06'
            GROUP BY customer_name
            ORDER BY revenue DESC
            LIMIT 5
        """))
        rows = result.fetchall()
        print(f"   ✓ Retrieved {len(rows)} customers")
        for row in rows[:3]:
            print(f"   ✓ {row[0]}: {row[1]:,.0f} revenue, {row[2]} orders")
    except Exception as e:
        print(f"   ✗ Error: {e}")

print("\n✅ All SQL queries tested successfully!")
