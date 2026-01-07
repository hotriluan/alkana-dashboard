from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    cooispi_df = pd.read_sql_table('raw_cooispi', db.bind)
    
    # Get a P01 order
    p01 = cooispi_df[cooispi_df['mrp_controller'] == 'P01'].iloc[0]
    
    print(f"=== P01 ORDER ===")
    print(f"Order: {p01['order']}")
    print(f"Batch: {p01['batch']}")
    
    # Try 1: Search by ORDER in reference
    print(f"\n=== SEARCH BY ORDER NUMBER IN REFERENCE ===")
    by_order = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_12_reference'].astype(str).str.contains(str(p01['order']), na=False))
    ]
    print(f"Found: {len(by_order)} records")
    
    # Try 2: Search by BATCH in reference
    print(f"\n=== SEARCH BY BATCH NUMBER IN REFERENCE ===")
    by_batch = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_12_reference'].astype(str).str.contains(str(p01['batch']), na=False))
    ]
    print(f"Found: {len(by_batch)} records")
    
    if not by_batch.empty:
        print("\nConsumed batches (P02):")
        print(by_batch[['col_0_posting_date', 'col_6_batch', 'col_4_material', 'col_12_reference']].head(10))
        
        # Check if these are P02
        p02_batches = by_batch['col_6_batch'].unique()
        print(f"\nUnique batches: {list(p02_batches)}")
        
        for batch in p02_batches:
            order_info = cooispi_df[cooispi_df['batch'] == batch]
            if not order_info.empty:
                mrp = order_info.iloc[0]['mrp_controller']
                print(f"  {batch} → {mrp}")
    
    # Try 3: Check if P01 batch appears in reference with # prefix
    print(f"\n=== SEARCH WITH # PREFIX ===")
    batch_with_hash = f"#{p01['batch']}"
    by_hash = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_12_reference'].astype(str).str.contains(batch_with_hash, na=False))
    ]
    print(f"Found: {len(by_hash)} records")
    
finally:
    db.close()
