"""
Sample customer data extraction for audit report
"""
import psycopg2
import json

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="alkana_dashboard",
    user="postgres",
    password="password123"
)

cur = conn.cursor()

# Query top 5 customers with old vs new method
query = """
SELECT 
    customer_name,
    COUNT(DISTINCT billing_document) as billing_docs_old_method,
    COUNT(DISTINCT so_number) as sales_orders_new_method,
    ROUND(SUM(net_value)::numeric, 2) as revenue
FROM fact_billing
WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'
    AND customer_name IS NOT NULL
GROUP BY customer_name
ORDER BY revenue DESC
LIMIT 5;
"""

cur.execute(query)
results = cur.fetchall()

print("=" * 80)
print("TOP 5 CUSTOMERS - OLD vs NEW COUNTING METHOD")
print("=" * 80)
print(f"{'Customer Name':<30} {'Old (Billing Docs)':<20} {'New (Sales Orders)':<20} {'Revenue':>10}")
print("-" * 80)

for row in results:
    customer, old_count, new_count, revenue = row
    print(f"{customer:<30} {old_count:<20} {new_count:<20} {revenue:>10,.2f}")

print("=" * 80)

# Get total to verify consistency
cur.execute("""
    SELECT COUNT(DISTINCT so_number) as total_orders_global
    FROM fact_billing
    WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'
        AND so_number IS NOT NULL;
""")
total_result = cur.fetchone()
print(f"\nConsistency Check:")
print(f"Global KPI count (direct query): {total_result[0] if total_result else 0}")
print(f"Expected (ground truth): 3,564")
print(f"Match: {'YES ✓' if total_result and total_result[0] == 3564 else 'NO ✗'}")

cur.close()
conn.close()
