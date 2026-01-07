from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    cooispi_df = pd.read_sql_table('raw_cooispi', db.bind)
    
    # Get MVT 261
    mvt_261 = mb51_df[mb51_df['col_1_mvt_type'] == 261].copy()
    
    print("=== MVT 261 SAMPLE DATA (20 records) ===\n")
    
    # Show all relevant columns
    cols = ['col_0_posting_date', 'col_1_mvt_type', 'col_2_plant', 'col_4_material', 
            'col_6_batch', 'col_7_qty', 'col_11_material_doc', 'col_12_reference']
    
    sample = mvt_261[cols].head(20)
    
    for idx, row in sample.iterrows():
        print(f"Record {idx}:")
        for col in cols:
            print(f"  {col}: {row[col]}")
        print()
    
    # Check if there are any patterns in reference field
    print("\n=== REFERENCE FIELD PATTERNS ===")
    print("Non-null references:")
    non_null = mvt_261[mvt_261['col_12_reference'].notna()]['col_12_reference'].head(30)
    for ref in non_null:
        print(f"  '{ref}'")
    
    # Check P01, P02, P03 batches in COOISPI
    print("\n=== SAMPLE BATCHES FROM COOISPI ===")
    for mrp in ['P01', 'P02', 'P03']:
        batches = cooispi_df[cooispi_df['mrp_controller'] == mrp]['batch'].head(5)
        print(f"\n{mrp} batches:")
        for batch in batches:
            print(f"  {batch}")
            
            # Check if this batch appears in MVT 261
            in_mvt = mvt_261[mvt_261['col_6_batch'] == batch]
            print(f"    → In MVT 261: {len(in_mvt)} records")
            
            if not in_mvt.empty:
                print(f"    → Reference values: {in_mvt['col_12_reference'].unique()}")
        
finally:
    db.close()
