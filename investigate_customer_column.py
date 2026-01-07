"""
Step 1: Investigate Excel column names to find customer column
"""
import pandas as pd

df = pd.read_excel("demodata/zrsd002.xlsx")

print("="*80)
print("EXCEL COLUMN INVESTIGATION")
print("="*80)

print(f"\nTotal columns: {len(df.columns)}")
print(f"Total rows: {len(df)}")

print("\n" + "="*80)
print("ALL COLUMNS:")
print("="*80)
for i, col in enumerate(df.columns, 1):
    non_null = df[col].notna().sum()
    pct = (non_null / len(df) * 100)
    print(f"{i:2d}. {col:40s} - {non_null:6,} non-null ({pct:5.1f}%)")

print("\n" + "="*80)
print("CUSTOMER-RELATED COLUMNS:")
print("="*80)

customer_keywords = ['customer', 'sold', 'party', 'name', 'payer', 'buyer']
found_cols = []

for col in df.columns:
    col_lower = col.lower()
    if any(keyword in col_lower for keyword in customer_keywords):
        found_cols.append(col)
        non_null = df[col].notna().sum()
        unique = df[col].nunique()
        print(f"\n📋 Column: '{col}'")
        print(f"   Non-null: {non_null:,} ({non_null/len(df)*100:.1f}%)")
        print(f"   Unique values: {unique:,}")
        print(f"   Sample values:")
        for val in df[col].dropna().head(5):
            print(f"     - {val}")

if not found_cols:
    print("\n⚠ NO customer-related columns found with standard keywords!")
    print("\nChecking first 20 columns for possible customer data...")
    for col in df.columns[:20]:
        unique = df[col].nunique()
        if 100 < unique < 5000:  # Likely customer count range
            print(f"\n   Possible: '{col}' - {unique} unique values")
            print(f"   Sample: {df[col].dropna().head(3).tolist()}")
