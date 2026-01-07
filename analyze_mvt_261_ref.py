from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    cooispi_df = pd.read_sql_table('raw_cooispi', db.bind)
    
    # Get MVT 261 records
    mvt_261 = mb51_df[mb51_df['col_1_mvt_type'] == 261].copy()
    
    print(f"=== MVT 261 ANALYSIS ===")
    print(f"Total MVT 261: {len(mvt_261)}")
    
    # Check reference field values
    print(f"\n=== REFERENCE FIELD VALUES ===")
    ref_values = mvt_261['col_12_reference'].value_counts().head(20)
    for ref, count in ref_values.items():
        print(f"  '{ref}': {count} records")
    
    # Check if any reference matches P01 order format
    print(f"\n=== CHECKING P01 ORDER FORMAT ===")
    p01_orders = cooispi_df[cooispi_df['mrp_controller'] == 'P01']['order'].head(10)
    print("Sample P01 orders:")
    for order in p01_orders:
        print(f"  {order}")
        
        # Check if this order appears in MVT 261 reference
        matches = mvt_261[mvt_261['col_12_reference'] == str(order)]
        print(f"    → MVT 261 matches: {len(matches)}")
        
    # Check what's in col_12_reference for MVT 261
    print(f"\n=== SAMPLE MVT 261 WITH NON-NULL REFERENCE ===")
    non_null_ref = mvt_261[mvt_261['col_12_reference'].notna()]
    print(f"Non-null references: {len(non_null_ref)}")
    
    if not non_null_ref.empty:
        print("\nSample:")
        print(non_null_ref[['col_0_posting_date', 'col_6_batch', 'col_4_material', 'col_12_reference']].head(20))
        
finally:
    db.close()
