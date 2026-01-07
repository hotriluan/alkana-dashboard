from src.db.connection import engine
import pandas as pd

# Extract customer name from raw_data JSON field
query = """
SELECT 
    raw_data->>'Bill-to' as customer_code,
    raw_data->>'Name of Bill to' as customer_name,
    raw_data->>'Dist Channel' as division_code,
    raw_data->>'Sales Office' as sales_office,
    COUNT(*) as records
FROM raw_zrsd002
WHERE raw_data->>'Name of Bill to' IS NOT NULL
GROUP BY 
    raw_data->>'Bill-to',
    raw_data->>'Name of Bill to',
    raw_data->>'Dist Channel',
    raw_data->>'Sales Office'
ORDER BY records DESC
LIMIT 10
"""

df = pd.read_sql(query, engine)
print("Customer data from raw_zrsd002:")
print(df.to_string())
