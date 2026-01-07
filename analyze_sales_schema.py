"""
CLAUDE KIT: Database + Sequential Thinking
Analyze fact_billing schema to design proper date filter query

Skills: Database, SQL, Backend Development
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:password123@localhost:5432/alkana_dashboard"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("CLAUDE KIT: Sales Performance Date Filter - Schema Analysis")
print("Skills: Database, Sequential Thinking")
print("=" * 80)

with engine.connect() as conn:
    # Step 1: Check fact_billing columns
    print("\n[STEP 1] fact_billing schema:")
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'fact_billing'
        ORDER BY ordinal_position
    """)).fetchall()
    
    for col in result:
        print(f"  {col[0]}: {col[1]}")
    
    # Step 2: Check sample data
    print("\n[STEP 2] Sample billing data:")
    result = conn.execute(text("""
        SELECT 
            billing_date,
            customer_name,
            salesman_name,
            net_value,
            billing_qty
        FROM fact_billing
        ORDER BY billing_date DESC
        LIMIT 5
    """)).fetchall()
    
    for row in result:
        print(f"  {row[0]} | {row[1][:30]} | {row[2]} | {row[3]:,.0f}")
    
    # Step 3: Test aggregation query with date filter
    print("\n[STEP 3] Test date-filtered aggregation:")
    result = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT billing_document) as total_invoices,
            COUNT(DISTINCT customer_name) as total_customers,
            SUM(net_value) as total_sales,
            AVG(net_value) as avg_order_value
        FROM fact_billing
        WHERE billing_date BETWEEN '2025-12-01' AND '2026-01-06'
    """)).fetchone()
    
    print(f"  Total Invoices: {result[0]}")
    print(f"  Total Customers: {result[1]}")
    print(f"  Total Sales: {result[2]:,.0f}")
    print(f"  Avg Order Value: {result[3]:,.2f}")
    
    # Step 4: Test customer-level aggregation
    print("\n[STEP 4] Top 5 customers (date filtered):")
    result = conn.execute(text("""
        SELECT 
            customer_name,
            COUNT(DISTINCT billing_document) as order_count,
            SUM(net_value) as sales_amount,
            SUM(billing_qty) as total_qty
        FROM fact_billing
        WHERE billing_date BETWEEN '2025-12-01' AND '2026-01-06'
        GROUP BY customer_name
        ORDER BY sales_amount DESC
        LIMIT 5
    """)).fetchall()
    
    for i, row in enumerate(result, 1):
        print(f"  {i}. {row[0][:40]}: {row[2]:,.0f} ({row[1]} orders)")

print("\n" + "=" * 80)
print("✅ Schema analysis complete - Ready to implement")
print("=" * 80)
