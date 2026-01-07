from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    
    print("=== MB51 MVT TYPE DISTRIBUTION ===")
    mvt_counts = mb51_df['col_1_mvt_type'].value_counts().sort_index()
    
    for mvt, count in mvt_counts.items():
        print(f"MVT {mvt}: {count} records")
        
    # Check specifically for 261
    mvt_261 = mb51_df[mb51_df['col_1_mvt_type'] == 261]
    print(f"\n=== MVT 261 (Consumption) ===")
    print(f"Total: {len(mvt_261)} records")
    
    if not mvt_261.empty:
        print("\nSample MVT 261:")
        print(mvt_261[['col_0_posting_date', 'col_6_batch', 'col_4_material', 'col_12_reference']].head(10))
    
finally:
    db.close()
