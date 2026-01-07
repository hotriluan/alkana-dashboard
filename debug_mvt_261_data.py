import pandas as pd

# Load MB51 data
mb51_df = pd.read_excel('demodata/mb51.XLSX')

print("=== MB51 DATA STRUCTURE CHECK ===\n")

# Check Movement Type values
print("Unique Movement Types:")
mvt_types = mb51_df['Movement Type'].value_counts()
print(mvt_types)

print("\n=== MVT 261 ANALYSIS ===\n")

# Get MVT 261 transactions
mvt_261 = mb51_df[mb51_df['Movement Type'] == 261]
print(f"Total MVT 261 transactions: {len(mvt_261)}")

if len(mvt_261) > 0:
    print(f"\nPlant distribution:")
    print(mvt_261['Plant'].value_counts())
    
    print(f"\nSample MVT 261 transactions:")
    print(mvt_261[['Batch', 'Plant', 'Material Description', 'Qty in Un. of Entry', 'Reference']].head(10))
    
    # Check for P02 batches (those at plant 1201)
    mvt_261_p1201 = mvt_261[mvt_261['Plant'] == 1201]
    print(f"\nMVT 261 @ Plant 1201: {len(mvt_261_p1201)}")
    
    if len(mvt_261_p1201) > 0:
        print("\nSample:")
        print(mvt_261_p1201[['Batch', 'Material Description', 'Qty in Un. of Entry', 'Reference']].head(5))
        
        # Get unique batches
        p02_batches = mvt_261_p1201['Batch'].unique()
        print(f"\nUnique P02 batches: {len(p02_batches)}")
        
        # Analyze one P02 batch in detail
        if len(p02_batches) > 0:
            sample_p02 = p02_batches[0]
            print(f"\n=== DETAILED ANALYSIS: {sample_p02} ===\n")
            
            # All transactions for this batch
            batch_txns = mb51_df[mb51_df['Batch'] == sample_p02]
            print(f"Total transactions: {len(batch_txns)}\n")
            
            for idx, row in batch_txns.iterrows():
                print(f"MVT {row['Movement Type']} @ Plant {row['Plant']}")
                print(f"  Material: {row['Material Description']}")
                print(f"  Qty: {row['Qty in Un. of Entry']} {row['Unit of Entry']}")
                print(f"  Mat Doc: {row['Material Document']}")
                print(f"  Reference: {row['Reference']}")
                print()
else:
    print("No MVT 261 transactions found!")
    print("\nChecking what movement types exist:")
    print(mb51_df['Movement Type'].unique())
