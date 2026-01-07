from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    cooispi_df = pd.read_sql_table('raw_cooispi', db.bind)
    
    print("=== COOISPI COLUMNS ===")
    print(cooispi_df.columns.tolist())
    
    print("\n=== SAMPLE P01 ORDER ===")
    p01 = cooispi_df[cooispi_df['mrp_controller'] == 'P01'].iloc[0]
    
    for col in cooispi_df.columns:
        print(f"{col}: {p01[col]}")
    
finally:
    db.close()
