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
    
    # Find MVT 261 where the OUTPUT batch is P01 batch
    # This means materials were consumed TO PRODUCE this P01 batch
    print(f"\n=== FINDING MATERIALS CONSUMED TO PRODUCE P01 BATCH ===")
    
    # MVT 261 with reference containing P01 batch
    consumption = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_12_reference'].astype(str).str.contains(p01['batch'], na=False))
    ]
    
    print(f"MVT 261 with reference containing '{p01['batch']}': {len(consumption)}")
    
    if not consumption.empty:
        print("\nConsumed batches (P02):")
        print(consumption[['col_0_posting_date', 'col_6_batch', 'col_4_material', 'col_12_reference']].head(10))
        
        # Get unique batches
        p02_batches = consumption['col_6_batch'].dropna().unique()
        print(f"\nUnique P02 batches: {list(p02_batches)}")
        
finally:
    db.close()
