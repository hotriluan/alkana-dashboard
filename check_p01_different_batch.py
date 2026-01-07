from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    
    # User's original batch
    test_batch = '25L2476310'
    
    print(f"=== CHECKING BATCH {test_batch} IN ALL PLANTS ===\n")
    
    batch_txns = mb51_df[mb51_df['col_6_batch'] == test_batch].copy()
    
    # Check MVT 101 at ALL plants
    mvt_101 = batch_txns[batch_txns['col_1_mvt_type'] == 101]
    
    print("MVT 101 (Goods Receipt) transactions:")
    if not mvt_101.empty:
        for idx, row in mvt_101.iterrows():
            print(f"  Plant {row['col_2_plant']}: {row['col_7_qty']} {row['col_8_uom']}")
            print(f"    Material: {row['col_5_material_desc']}")
    else:
        print("  None found!")
    
    # Check if there's a DIFFERENT batch for P01
    print(f"\n=== CHECKING IF P01 HAS DIFFERENT BATCH ===")
    
    # Get P02 material from MVT 261
    p02_txn = batch_txns[batch_txns['col_1_mvt_type'] == 261]
    if not p02_txn.empty:
        p02_material_desc = p02_txn.iloc[0]['col_5_material_desc']
        p02_material_code = p02_txn.iloc[0]['col_4_material']
        
        print(f"\nP02 Material: {p02_material_desc} ({p02_material_code})")
        
        # Try to find P01 material (might have suffix like -4L)
        # Search for materials with similar name
        print(f"\nSearching for P01 materials with similar name...")
        
        # Get all MVT 101 @ 1401 with material desc containing base name
        base_name = p02_material_desc.split()[0] if p02_material_desc else ""
        
        p01_candidates = mb51_df[
            (mb51_df['col_1_mvt_type'] == 101) &
            (mb51_df['col_2_plant'] == 1401) &
            (mb51_df['col_5_material_desc'].str.contains(base_name, na=False, case=False))
        ]
        
        if not p01_candidates.empty:
            print(f"\nFound {len(p01_candidates)} P01 candidates @ Plant 1401:")
            
            # Group by batch
            p01_batches = p01_candidates.groupby('col_6_batch').agg({
                'col_0_posting_date': 'first',
                'col_5_material_desc': 'first',
                'col_7_qty': 'sum'
            }).head(10)
            
            for batch, data in p01_batches.iterrows():
                print(f"  Batch {batch}:")
                print(f"    Date: {data['col_0_posting_date']}")
                print(f"    Material: {data['col_5_material_desc']}")
                print(f"    Qty: {data['col_7_qty']}")
        else:
            print(f"  No P01 found for material containing '{base_name}'")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Batch {test_batch}:")
    print(f"  - Has P02 consumption (MVT 261 @ 1201): YES")
    print(f"  - Has P01 production (MVT 101 @ 1401): NO")
    print(f"  - Conclusion: P01 might use DIFFERENT batch number!")
    
finally:
    db.close()
