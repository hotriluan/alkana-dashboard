"""
Comparison of expected vs actual column names in zrsd004.XLSX
"""

print("=" * 100)
print("COLUMN NAME MISMATCH ANALYSIS")
print("=" * 100)

# What the loader expects
loader_expects = [
    'Actual GI Date',
    'Delivery',
    'Line Item',
    'SO Reference',
    'Shipping Point',
    'SLoc',
    'Sales Office',
    'Distribution Channel',  # ← WRONG
    'Cust. Group',
    'Sold-to Party',
    'Ship-to Party',
    'Ship-to Name',          # ← WRONG
    'Ship-to City',          # ← WRONG
    'Salesman ID',
    'Salesman Name',
    'Material',
    'Material Description',  # ← WRONG
    'Delivery Qty',
    'Tonase',
    'Tonase Unit',
    'Net Weight',
    'Volume',
    'Prod. Hierarchy',       # ← WRONG
]

# What the Excel file actually has
file_has = [
    'Delivery Date',
    'Actual GI Date',
    'Delivery',
    'SO Reference',
    'Req. Type',
    'Delivery Type',
    'Shipping Point',
    'Sloc',
    'Sales Office',
    'Dist. Channel',         # ← ACTUAL NAME
    'Cust. Group',
    'Sold-to Party',
    'Ship-to Party',
    'Name of Ship-to',       # ← ACTUAL NAME
    'City of Ship-to',       # ← ACTUAL NAME
    'Regional Stru. Grp.',
    'Transportation Zone',
    'Salesman ID',
    'Salesman Name',
    'Material',
    'Description',           # ← ACTUAL NAME
    'Delivery Qty',
    'Tonase',
    'Tonase Unit',
    'Actual Delivery Qty',
    'Sales Unit',
    'Net Weight',
    'Weight Unit',
    'Volume',
    'Volume Unit',
    'Created By',
    'Product Hierarchy',     # ← ACTUAL NAME
    'Line Item',
    'Total Movement Goods Stat'
]

print("\nMISMATCHES:")
print("-" * 100)
mismatches = [
    ('Distribution Channel', 'Dist. Channel'),
    ('Ship-to Name', 'Name of Ship-to'),
    ('Ship-to City', 'City of Ship-to'),
    ('Material Description', 'Description'),
    ('Prod. Hierarchy', 'Product Hierarchy'),
]

for expected, actual in mismatches:
    print(f"  Loader expects: '{expected:25s}' → File has: '{actual}'")

print("\nMISSING IN LOADER (file has these columns):")
print("-" * 100)
missing = [
    'Delivery Date',
    'Req. Type',
    'Delivery Type',
    'Regional Stru. Grp.',
    'Transportation Zone',
    'Actual Delivery Qty',
    'Sales Unit',
    'Weight Unit',
    'Volume Unit',
    'Created By',
    'Total Movement Goods Stat'
]
for col in missing:
    print(f"  - {col}")

print("\n" + "=" * 100)
print("IMPACT:")
print("=" * 100)
print("""
Because pandas cannot read the headers (returns 'Unnamed: 0', 'Unnamed: 1', ...),
all row.get() calls in the loader return None:

  - row.get('Delivery')           → None (should be '1410005383')
  - row.get('Actual GI Date')     → None (should be datetime)
  - row.get('Dist. Channel')      → None (should be '99')
  - etc.

Result: Database gets inserted with all NULL values except source metadata.
""")
