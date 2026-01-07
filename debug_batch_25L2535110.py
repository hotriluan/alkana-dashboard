import pandas as pd

# Load MB51 data
mb51_df = pd.read_excel('demodata/mb51.XLSX')

# Check batch 25L2535110
batch = '25L2535110'

print(f"=== ANALYZING BATCH {batch} ===\n")

batch_data = mb51_df[mb51_df['Batch'] == batch].copy()

print(f"Total transactions: {len(batch_data)}\n")

# Show all transactions
for idx, row in batch_data.iterrows():
    print(f"Date: {row['Posting Date']}")
    print(f"  MVT: {row['Move Type']}")
    print(f"  Plant: {row['Plant']}")
    print(f"  Material: {row['Material Description']}")
    print(f"  Qty: {row['Qty in Un. of Entry']} {row['Unit of Entry']}")
    print(f"  Mat Doc: {row['Material Document']}")
    print()

# Calculate what our logic would use
print("=== OUR LOGIC ===\n")

# P02 Consumption (MVT 261 @ 1201)
p02_consumption = batch_data[
    (batch_data['Move Type'] == 261) &
    (batch_data['Plant'] == 1201)
]

if not p02_consumption.empty:
    p02_qty = abs(p02_consumption['Qty in Un. of Entry'].sum())
    print(f"P02 Consumed (MVT 261 @ 1201): {p02_qty} KG")
else:
    print("No P02 consumption found")

# P01 Production (MVT 101 @ 1401)
p01_batch = '25L2535010'
p01_data = mb51_df[mb51_df['Batch'] == p01_batch]

p01_production = p01_data[
    (p01_data['Move Type'] == 101) &
    (p01_data['Plant'] == 1401)
]

if not p01_production.empty:
    p01_qty = p01_production['Qty in Un. of Entry'].sum()
    p01_uom = p01_production.iloc[0]['Unit of Entry']
    print(f"P01 Produced (MVT 101 @ 1401): {p01_qty} {p01_uom}")
    
    # Assuming conversion: 1 PC = ~6 KG (need to check UOM table)
    # From your image: 24 PC should convert to some KG value
    print(f"\nIf 24 PC = 144 KG (6 KG/PC):")
    print(f"  Yield = 144 / 149.164 = {144/149.164*100:.2f}%")
    print(f"\nIf 24 PC = 791.4 KG equivalent:")
    print(f"  Yield = 791.4 / 791.4 = 100%")
else:
    print("No P01 production found")

# Check P02 Production (MVT 101 @ 1201) - this might be the correct input
p02_production = batch_data[
    (batch_data['Move Type'] == 101) &
    (batch_data['Plant'] == 1201)
]

if not p02_production.empty:
    p02_produced = p02_production['Qty in Un. of Entry'].sum()
    print(f"\n=== ALTERNATIVE: P02 PRODUCED ===")
    print(f"P02 Produced (MVT 101 @ 1201): {p02_produced} KG")
    print(f"This might be the ACTUAL input to P01 process")
