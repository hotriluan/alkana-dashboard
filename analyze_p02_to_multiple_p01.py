# -*- coding: utf-8 -*-
import pandas as pd

# Load MB51 data
mb51_df = pd.read_excel('demodata/mb51.XLSX')

print("=== P02 TO MULTIPLE P01 ANALYSIS ===\n")

# Get MVT 261 transactions (P02 consumption) - STRING comparison
mvt_261 = mb51_df[
    (mb51_df['Movement Type'].astype(str) == '261') &
    (mb51_df['Plant'] == 1201)
]

print(f"Total MVT 261 @ Plant 1201: {len(mvt_261)}")

# Get unique P02 batches
p02_batches = mvt_261['Batch'].unique()
print(f"Unique P02 batches: {len(p02_batches)}\n")

# Analyze a few P02 batches to see consumption pattern
print("=== SAMPLE P02 BATCHES ===\n")

for p02_batch in p02_batches[:3]:
    print(f"P02 Batch: {p02_batch}")
    
    # Get all MVT 261 for this batch
    p02_consumptions = mvt_261[mvt_261['Batch'] == p02_batch]
    
    total_consumed = abs(p02_consumptions['Qty in Un. of Entry'].sum())
    p02_material = p02_consumptions.iloc[0]['Material Description']
    
    print(f"  Material: {p02_material}")
    print(f"  Total consumed: {total_consumed} KG")
    print(f"  Number of consumption transactions: {len(p02_consumptions)}")
    
    # Show each consumption transaction with Reference
    print(f"  Consumption details:")
    for idx, row in p02_consumptions.iterrows():
        print(f"    - {abs(row['Qty in Un. of Entry'])} KG, Mat Doc: {row['Material Document']}, Ref: {row['Reference']}")
    
    # Try to find related P01 batches using sequential pattern
    prefix = p02_batch[:6]
    try:
        two_digits = int(p02_batch[6:8])
        suffix = p02_batch[8:]
        
        print(f"\n  Checking P01 batches (sequential pattern):")
        found_p01 = []
        
        # Check P01 candidates from -1 to -10
        for offset in range(1, 11):
            p01_candidate = f"{prefix}{two_digits - offset:02d}{suffix}"
            
            p01_exists = mb51_df[
                (mb51_df['Batch'] == p01_candidate) &
                (mb51_df['Movement Type'].astype(str) == '101') &
                (mb51_df['Plant'] == 1401)
            ]
            
            if not p01_exists.empty:
                p01_qty = p01_exists['Qty in Un. of Entry'].sum()
                p01_uom = p01_exists.iloc[0]['Unit of Entry']
                p01_material = p01_exists.iloc[0]['Material Description']
                
                found_p01.append({
                    'batch': p01_candidate,
                    'qty': p01_qty,
                    'uom': p01_uom,
                    'material': p01_material,
                    'offset': offset
                })
                
                print(f"    Offset -{offset}: {p01_candidate} = {p01_qty} {p01_uom} ({p01_material})")
        
        if found_p01:
            print(f"\n  Found {len(found_p01)} P01 batches for this P02!")
        else:
            print(f"  No P01 batches found")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n" + "="*80 + "\n")

# Summary statistics
print("=== SUMMARY STATISTICS ===\n")

# Count how many P01 batches each P02 can link to
p02_to_p01_counts = {}

for p02_batch in p02_batches[:50]:  # Test first 50
    prefix = p02_batch[:6]
    try:
        two_digits = int(p02_batch[6:8])
        suffix = p02_batch[8:]
        
        count = 0
        for offset in range(1, 11):
            p01_candidate = f"{prefix}{two_digits - offset:02d}{suffix}"
            
            p01_exists = mb51_df[
                (mb51_df['Batch'] == p01_candidate) &
                (mb51_df['Movement Type'].astype(str) == '101') &
                (mb51_df['Plant'] == 1401)
            ]
            
            if not p01_exists.empty:
                count += 1
        
        p02_to_p01_counts[p02_batch] = count
    except:
        pass

# Distribution
from collections import Counter
distribution = Counter(p02_to_p01_counts.values())

print("P02 to P01 relationship distribution:")
for num_p01, count in sorted(distribution.items()):
    print(f"  {num_p01} P01 batches: {count} P02 batches")
