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
    print(f"Material: {p01['material']}")
    
    # Check COOISPI for components consumed
    print(f"\n=== CHECKING COOISPI FOR COMPONENTS ===")
    # COOISPI might have BOM (Bill of Materials) info
    print(f"COOISPI columns: {cooispi_df.columns.tolist()}")
    
    # Check MB51 for consumption by batch (not order)
    print(f"\n=== MVT 261 FOR THIS P01 BATCH ===")
    mvt_261_batch = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_6_batch'] == p01['batch'])
    ]
    print(f"Found: {len(mvt_261_batch)} records")
    
    if not mvt_261_batch.empty:
        print("\nConsumption records:")
        print(mvt_261_batch[['col_0_posting_date', 'col_6_batch', 'col_4_material', 'col_7_qty']].head())
        
finally:
    db.close()
