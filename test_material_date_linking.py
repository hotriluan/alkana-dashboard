# -*- coding: utf-8 -*-
import pandas as pd
from datetime import timedelta

# Load MB51 data
mb51_df = pd.read_excel('demodata/mb51.XLSX')

print("=== ALTERNATIVE LINKING APPROACH ===\n")
print("Strategy: Link P02 consumption to P01 production by:")
print("1. Material name matching (P01 = P02 + suffix)")
print("2. Date proximity (within 7 days)")
print("3. Quantity correlation\n")

# Get P02 consumption (MVT 261 @ 1201)
p02_consumptions = mb51_df[
    (mb51_df['Movement Type'].astype(str) == '261') &
    (mb51_df['Plant'] == 1201)
].copy()

# Get P01 production (MVT 101 @ 1401)
p01_productions = mb51_df[
    (mb51_df['Movement Type'].astype(str) == '101') &
    (mb51_df['Plant'] == 1401)
].copy()

print(f"P02 consumptions: {len(p02_consumptions)}")
print(f"P01 productions: {len(p01_productions)}\n")

# Group P02 by batch
p02_by_batch = p02_consumptions.groupby('Batch').agg({
    'Qty in Un. of Entry': lambda x: abs(x.sum()),
    'Material Description': 'first',
    'Posting Date': 'first',
    'Material': 'first'
}).reset_index()

p02_by_batch.columns = ['p02_batch', 'p02_qty_kg', 'p02_material_desc', 'p02_date', 'p02_material_code']

print("=== TESTING MATERIAL-BASED LINKING ===\n")

# Test first 5 P02 batches
matches_found = 0

for idx, p02_row in p02_by_batch.head(10).iterrows():
    p02_batch = p02_row['p02_batch']
    p02_material = p02_row['p02_material_desc']
    p02_qty = p02_row['p02_qty_kg']
    p02_date = pd.to_datetime(p02_row['p02_date'])
    
    print(f"P02 Batch: {p02_batch}")
    print(f"  Material: {p02_material}")
    print(f"  Qty: {p02_qty} KG")
    print(f"  Date: {p02_date.date()}")
    
    # Find P01 with matching material name (starts with P02 material)
    p01_matches = p01_productions[
        p01_productions['Material Description'].str.startswith(p02_material, na=False)
    ].copy()
    
    if not p01_matches.empty:
        # Filter by date proximity (within 7 days)
        p01_matches['date_diff'] = abs(
            (pd.to_datetime(p01_matches['Posting Date']) - p02_date).dt.days
        )
        
        close_matches = p01_matches[p01_matches['date_diff'] <= 7]
        
        if not close_matches.empty:
            print(f"  Found {len(close_matches)} P01 candidates:")
            matches_found += 1
            
            for _, p01_row in close_matches.head(5).iterrows():
                print(f"    - Batch: {p01_row['Batch']}")
                print(f"      Material: {p01_row['Material Description']}")
                print(f"      Qty: {p01_row['Qty in Un. of Entry']} {p01_row['Unit of Entry']}")
                print(f"      Date: {pd.to_datetime(p01_row['Posting Date']).date()} (Δ{p01_row['date_diff']} days)")
        else:
            print(f"  No P01 within 7 days")
    else:
        print(f"  No P01 with matching material name")
    
    print()

print(f"\n=== RESULTS ===")
print(f"Tested: 10 P02 batches")
print(f"Matches found: {matches_found}")
print(f"Match rate: {matches_found/10*100:.1f}%")
