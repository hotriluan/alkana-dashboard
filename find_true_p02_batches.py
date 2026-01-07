# -*- coding: utf-8 -*-
import pandas as pd

# Load MB51 and COOISPI data
mb51_df = pd.read_excel('demodata/mb51.XLSX')
cooispi_df = pd.read_excel('demodata/cooispi.XLSX')

print("=== FINDING TRUE P02 SEMI-FINISHED BATCHES ===\n")

# Strategy: Use COOISPI to identify P02 batches (MRP Controller = P02)
p02_orders = cooispi_df[cooispi_df['MRP Controller'] == 'P02']

print(f"P02 orders in COOISPI: {len(p02_orders)}")
print(f"Unique P02 batches: {p02_orders['Batch'].nunique()}\n")

# Get P02 batches from COOISPI
p02_batches_from_cooispi = set(p02_orders['Batch'].dropna().unique())

print("Sample P02 batches from COOISPI:")
for batch in list(p02_batches_from_cooispi)[:5]:
    print(f"  {batch}")

# Now find these batches in MB51 MVT 261
print("\n=== P02 CONSUMPTION IN MB51 ===\n")

mvt_261 = mb51_df[
    (mb51_df['Movement Type'].astype(str) == '261') &
    (mb51_df['Plant'] == 1201)
]

# Filter to only P02 batches
p02_mvt_261 = mvt_261[mvt_261['Batch'].isin(p02_batches_from_cooispi)]

print(f"MVT 261 transactions for P02 batches: {len(p02_mvt_261)}")
print(f"Unique P02 batches with MVT 261: {p02_mvt_261['Batch'].nunique()}\n")

# Analyze a few P02 batches
p02_batches_with_consumption = p02_mvt_261['Batch'].unique()

print("=== ANALYZING P02 BATCHES ===\n")

for p02_batch in p02_batches_with_consumption[:5]:
    print(f"P02 Batch: {p02_batch}")
    
    # Get P02 order info from COOISPI
    p02_order = p02_orders[p02_orders['Batch'] == p02_batch].iloc[0]
    print(f"  Material: {p02_order['Material Description']}")
    print(f"  Order Qty: {p02_order['Order Quantity']} {p02_order['Unit of Measure']}")
    
    # Get consumption from MB51
    consumptions = p02_mvt_261[p02_mvt_261['Batch'] == p02_batch]
    total_consumed = abs(consumptions['Qty in Un. of Entry'].sum())
    print(f"  Total consumed (MVT 261): {total_consumed} KG")
    
    # Try sequential pattern for P01
    prefix = p02_batch[:6]
    try:
        two_digits = int(p02_batch[6:8])
        suffix = p02_batch[8:]
        
        print(f"  Looking for P01 batches:")
        found_any = False
        
        for offset in range(1, 6):
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
                found_any = True
                print(f"    Offset -{offset}: {p01_candidate} = {p01_qty} {p01_uom} ({p01_material})")
        
        if not found_any:
            print(f"    No P01 found with sequential pattern")
    except:
        pass
    
    print()
