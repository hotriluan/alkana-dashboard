from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    
    print("=== FINDING BATCHES WITH P02→P01 PATTERN ===\n")
    
    # Find batches that have BOTH:
    # 1. MVT 261 @ Plant 1201 (P02 consumption)
    # 2. MVT 101 @ Plant 1401 (P01 production)
    
    # Get batches with MVT 261 @ 1201
    p02_batches = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_2_plant'] == 1201)
    ]['col_6_batch'].unique()
    
    print(f"Batches with P02 consumption (MVT 261 @ 1201): {len(p02_batches)}")
    
    # Get batches with MVT 101 @ 1401
    p01_batches = mb51_df[
        (mb51_df['col_1_mvt_type'] == 101) &
        (mb51_df['col_2_plant'] == 1401)
    ]['col_6_batch'].unique()
    
    print(f"Batches with P01 production (MVT 101 @ 1401): {len(p01_batches)}")
    
    # Find intersection
    common_batches = set(p02_batches) & set(p01_batches)
    print(f"\nBatches with BOTH P02→P01: {len(common_batches)}")
    
    if common_batches:
        print(f"\nSample batches with P02→P01 pattern:")
        for batch in list(common_batches)[:5]:
            print(f"  {batch}")
        
        # Test first batch
        test_batch = list(common_batches)[0]
        print(f"\n=== DETAILED ANALYSIS: {test_batch} ===\n")
        
        batch_txns = mb51_df[mb51_df['col_6_batch'] == test_batch].copy()
        batch_txns = batch_txns.sort_values('col_0_posting_date')
        
        cols = ['col_0_posting_date', 'col_1_mvt_type', 'col_2_plant', 
                'col_5_material_desc', 'col_7_qty', 'col_8_uom']
        
        for idx, row in batch_txns[cols].iterrows():
            print(f"MVT {row['col_1_mvt_type']} @ Plant {row['col_2_plant']}:")
            print(f"  {row['col_5_material_desc']}")
            print(f"  Qty: {row['col_7_qty']} {row['col_8_uom']}")
            print()
        
        # Calculate yield
        p02_consumption = batch_txns[
            (batch_txns['col_1_mvt_type'] == 261) &
            (batch_txns['col_2_plant'] == 1201)
        ]
        
        p01_production = batch_txns[
            (batch_txns['col_1_mvt_type'] == 101) &
            (batch_txns['col_2_plant'] == 1401)
        ]
        
        if not p02_consumption.empty and not p01_production.empty:
            p02_qty = abs(p02_consumption['col_7_qty'].sum())
            p01_qty = p01_production['col_7_qty'].sum()
            p01_uom = p01_production.iloc[0]['col_8_uom']
            
            print("=== YIELD CALCULATION ===")
            print(f"P02 Input: {p02_qty} KG")
            print(f"P01 Output: {p01_qty} {p01_uom}")
            print(f"\nNote: Need UOM conversion to calculate exact yield")
    else:
        print("\n❌ NO batches found with both P02 consumption and P01 production!")
        print("\nLet's check what patterns exist:")
        
        # Check MVT 101 at different plants
        print("\n=== MVT 101 (GR) Distribution by Plant ===")
        mvt_101 = mb51_df[mb51_df['col_1_mvt_type'] == 101]
        plant_dist = mvt_101['col_2_plant'].value_counts()
        for plant, count in plant_dist.items():
            print(f"  Plant {plant}: {count} receipts")
        
finally:
    db.close()
