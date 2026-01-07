from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    
    # Test batch từ user
    test_batch = '25L2476310'
    
    print(f"=== ANALYZING BATCH: {test_batch} ===\n")
    
    # Get all transactions for this batch
    batch_txns = mb51_df[mb51_df['col_6_batch'] == test_batch].copy()
    batch_txns = batch_txns.sort_values('col_0_posting_date')
    
    print(f"Total transactions: {len(batch_txns)}\n")
    
    # Show all transactions
    cols = ['col_0_posting_date', 'col_1_mvt_type', 'col_2_plant', 
            'col_4_material', 'col_5_material_desc', 'col_7_qty', 
            'col_8_uom', 'col_11_material_doc']
    
    for idx, row in batch_txns[cols].iterrows():
        print(f"Transaction {idx}:")
        print(f"  Date: {row['col_0_posting_date']}")
        print(f"  MVT: {row['col_1_mvt_type']}")
        print(f"  Plant: {row['col_2_plant']}")
        print(f"  Material: {row['col_4_material']}")
        print(f"  Description: {row['col_5_material_desc']}")
        print(f"  Qty: {row['col_7_qty']} {row['col_8_uom']}")
        print(f"  Mat Doc: {row['col_11_material_doc']}")
        print()
    
    # Identify P02 consumption and P01 production
    print("=== YIELD CALCULATION ===\n")
    
    # P02 Consumption: MVT 261 @ Plant 1201
    p02_consumption = batch_txns[
        (batch_txns['col_1_mvt_type'] == 261) &
        (batch_txns['col_2_plant'] == 1201)
    ]
    
    if not p02_consumption.empty:
        p02_qty = abs(p02_consumption['col_7_qty'].sum())
        p02_material = p02_consumption.iloc[0]['col_5_material_desc']
        print(f"P02 Consumption (MVT 261 @ 1201):")
        print(f"  Material: {p02_material}")
        print(f"  Qty: {p02_qty} KG")
    else:
        print("No P02 consumption found!")
        p02_qty = None
    
    # P01 Production: MVT 101 @ Plant 1401
    p01_production = batch_txns[
        (batch_txns['col_1_mvt_type'] == 101) &
        (batch_txns['col_2_plant'] == 1401)
    ]
    
    if not p01_production.empty:
        p01_qty = p01_production['col_7_qty'].sum()
        p01_uom = p01_production.iloc[0]['col_8_uom']
        p01_material = p01_production.iloc[0]['col_5_material_desc']
        print(f"\nP01 Production (MVT 101 @ 1401):")
        print(f"  Material: {p01_material}")
        print(f"  Qty: {p01_qty} {p01_uom}")
    else:
        print("\nNo P01 production found!")
        p01_qty = None
    
    # Calculate yield (need UOM conversion)
    if p02_qty and p01_qty:
        print(f"\n=== YIELD (Need UOM Conversion) ===")
        print(f"P02 Input: {p02_qty} KG")
        print(f"P01 Output: {p01_qty} {p01_uom}")
        print(f"Note: Need to convert {p01_qty} {p01_uom} to KG for yield calculation")
    
finally:
    db.close()
