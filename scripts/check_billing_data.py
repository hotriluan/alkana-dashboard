from src.db.connection import engine
import pandas as pd

# Check fact_billing data
df = pd.read_sql('SELECT * FROM fact_billing LIMIT 100', engine)

print('Columns with non-null values:')
for col in df.columns:
    non_null = df[col].notna().sum()
    if non_null > 50:  # Show columns with >50% data
        sample_val = df[col].dropna().iloc[0] if non_null > 0 else None
        print(f'{col}: {non_null}/100 non-null, sample: {sample_val}')

print('\n=== Sample rows ===')
print(df[['salesman_name', 'sales_office', 'net_value', 'billing_qty', 'billing_document']].head(5))
