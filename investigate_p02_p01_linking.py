import pandas as pd

# Load MB51 data
mb51_df = pd.read_excel('demodata/mb51.XLSX')

print("=== INVESTIGATING P02 → MULTIPLE P01 PATTERN ===\n")

# Strategy: Look for P02 batches that have MVT 261 consumption
# Then find if there are MULTIPLE P01 batches that reference this P02

# Example: Take a P02 batch with MVT 261
p02_batches = mb51_df[
    (mb51_df['Movement Type'] == 261) &
    (mb51_df['Plant'] == 1201)
]['Batch'].unique()

print(f"Total P02 batches with MVT 261: {len(p02_batches)}\n")

# Check a few P02 batches to see their consumption pattern
print("=== ANALYZING SAMPLE P02 BATCHES ===\n")

for p02_batch in p02_batches[:5]:
    print(f"P02 Batch: {p02_batch}")
    
    # Get all MVT 261 transactions for this batch
    p02_txns = mb51_df[
        (mb51_df['Batch'] == p02_batch) &
        (mb51_df['Movement Type'] == 261) &
        (mb51_df['Plant'] == 1201)
    ]
    
    total_consumed = abs(p02_txns['Qty in Un. of Entry'].sum())
    print(f"  Total consumed: {total_consumed} KG")
    
    # Check Reference field - might contain P01 order info
    print(f"  Reference values:")
    for idx, row in p02_txns.iterrows():
        print(f"    Mat Doc: {row['Material Document']}, Ref: {row['Reference']}, Qty: {row['Qty in Un. of Entry']}")
    
    # Try to find related P01 batches using sequential pattern
    # P01 = P02 - 1
    prefix = p02_batch[:6]
    try:
        two_digits = int(p02_batch[6:8])
        suffix = p02_batch[8:]
        
        # Check P01 batches from -1 to -5
        print(f"  Checking potential P01 batches:")
        for offset in range(1, 6):
            p01_candidate = f"{prefix}{two_digits - offset:02d}{suffix}"
            
            p01_exists = mb51_df[
                (mb51_df['Batch'] == p01_candidate) &
                (mb51_df['Movement Type'] == 101) &
                (mb51_df['Plant'] == 1401)
            ]
            
            if not p01_exists.empty:
                p01_qty = p01_exists['Qty in Un. of Entry'].sum()
                p01_material = p01_exists.iloc[0]['Material Description']
                print(f"    ✓ {p01_candidate}: {p01_qty} PC - {p01_material}")
    except:
        pass
    
    print()

# Check if Material Document can link P02 consumption to P01 production
print("\n=== CHECKING MATERIAL DOCUMENT LINKING ===\n")

# Get a sample MVT 261 transaction
sample_261 = mb51_df[
    (mb51_df['Movement Type'] == 261) &
    (mb51_df['Plant'] == 1201)
].iloc[0]

print(f"Sample MVT 261:")
print(f"  Batch: {sample_261['Batch']}")
print(f"  Material Doc: {sample_261['Material Document']}")
print(f"  Reference: {sample_261['Reference']}")
print(f"  Qty: {sample_261['Qty in Un. of Entry']}")

# Try to find related MVT 101 with same material doc
related_101 = mb51_df[
    (mb51_df['Material Document'] == sample_261['Material Document']) &
    (mb51_df['Movement Type'] == 101)
]

print(f"\nRelated MVT 101 with same Material Document:")
if not related_101.empty:
    for idx, row in related_101.iterrows():
        print(f"  Batch: {row['Batch']}, Plant: {row['Plant']}, Qty: {row['Qty in Un. of Entry']}")
else:
    print("  None found")

# Check Reference field pattern
print("\n=== REFERENCE FIELD ANALYSIS ===\n")

# Get all MVT 261 references
mvt_261_refs = mb51_df[
    (mb51_df['Movement Type'] == 261) &
    (mb51_df['Plant'] == 1201)
]['Reference'].value_counts().head(10)

print("Top 10 Reference values in MVT 261:")
for ref, count in mvt_261_refs.items():
    print(f"  {ref}: {count} occurrences")
