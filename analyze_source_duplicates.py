"""
Analyze Source Data Duplicates

Skills: backend-development, databases
CLAUDE.md: Real Implementation - Find root cause in source data

Found: mb51.XLSX has MASSIVE duplicates!
- Material+Plant combinations: up to 395 duplicates
- This explains 2x (or more) duplication in fact tables
"""
import pandas as pd

print("=" * 80)
print("SOURCE DATA DUPLICATE ANALYSIS")
print("=" * 80)

# Analyze zrfi005.xlsx (AR data)
print("\n[FILE 1] zrfi005.xlsx - AR Aging Data")
print("-" * 80)

try:
    df = pd.read_excel('demodata/zrfi005.xlsx')
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Check for duplicate customers
    if 'Customer Name' in df.columns:
        unique_customers = df['Customer Name'].nunique()
        print(f"\nUnique customers: {unique_customers}")
        print(f"Duplicate ratio: {len(df) / unique_customers:.2f}x")
        
        # Find duplicates
        dups = df[df.duplicated(subset=['Customer Name'], keep=False)]
        if len(dups) > 0:
            print(f"❌ DUPLICATES FOUND: {len(dups)} rows")
            print("\nSample duplicate customers:")
            print(dups[['Customer Name', 'Total Target']].head(10))
        else:
            print("✅ No duplicate customers")
    
except Exception as e:
    print(f"Error: {e}")

# Analyze mb51.XLSX (Inventory data)
print("\n[FILE 2] mb51.XLSX - Inventory Movements")
print("-" * 80)

try:
    df = pd.read_excel('demodata/mb51.XLSX')
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)[:10]}")
    
    # Check for duplicate Material+Plant combinations
    if 'Material' in df.columns and 'Plant' in df.columns:
        mat_plant = df.groupby(['Material', 'Plant']).size()
        dups = mat_plant[mat_plant > 1]
        
        print(f"\nMaterial+Plant combinations with duplicates: {len(dups)}")
        print(f"Max duplicates for one combination: {dups.max() if len(dups) > 0 else 0}")
        
        if len(dups) > 0:
            print(f"❌ MASSIVE DUPLICATES FOUND!")
            print("\nTop 10 most duplicated combinations:")
            print(dups.sort_values(ascending=False).head(10))
            
            # This is EXPECTED for mb51 - it's a movement log!
            print("\n⚠️  IMPORTANT: mb51 is a MOVEMENT LOG, not a snapshot!")
            print("   Multiple rows for same Material+Plant is NORMAL")
            print("   Each row = one movement transaction")
            print("   Problem is in HOW we aggregate this data!")
        else:
            print("✅ No duplicates")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("ROOT CAUSE IDENTIFIED")
print("=" * 80)

print("""
PROBLEM: mb51.XLSX is a TRANSACTION LOG, not a snapshot!
- Each row = one inventory movement (101, 102, 261, 262, etc.)
- Same Material+Plant appears MANY times (395x!)
- transform_mb51() inserts ALL movements as separate records

CURRENT BEHAVIOR:
- transform_mb51() inserts 12,606 movement records
- fact_inventory has 12,606 rows
- Dashboard sums ALL movements → inflated totals!

CORRECT BEHAVIOR:
- fact_inventory should store CURRENT STOCK LEVELS
- Need to AGGREGATE movements by Material+Plant
- Calculate net stock: (receipts 101) - (issues 261) etc.

SOLUTION:
Fix transform_mb51() to aggregate movements into stock levels:
1. Group by Material+Plant
2. Sum stock_impact (101=+, 261=-, etc.)
3. Insert ONE row per Material+Plant with net stock
""")

print("=" * 80)
