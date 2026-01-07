from src.db.connection import engine
import pandas as pd

# Check if we can create meaningful sales data
query = """
SELECT 
    fb.cust_group as customer_code,
    COALESCE(dcg.description, 'Customer Group ' || fb.cust_group) as customer_name,
    fb.sales_office as division_code,
    SUM(fb.net_value) as total_sales,
    SUM(fb.billing_qty) as total_qty,
    COUNT(DISTINCT fb.billing_document) as orders
FROM fact_billing fb
LEFT JOIN dim_customer_group dcg ON fb.cust_group = dcg.group_code
WHERE fb.cust_group IS NOT NULL
GROUP BY fb.cust_group, dcg.description, fb.sales_office
ORDER BY total_sales DESC
LIMIT 10
"""

df = pd.read_sql(query, engine)
print("Sales by Customer Group:")
print(df.to_string())
print(f"\nTotal customer groups: {len(df)}")
