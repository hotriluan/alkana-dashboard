from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    # Check production_chain table
    chain_df = pd.read_sql_table('fact_production_chain', db.bind)
    
    print(f"=== FACT_PRODUCTION_CHAIN ===")
    print(f"Total records: {len(chain_df)}")
    
    if not chain_df.empty:
        print(f"\nColumns: {chain_df.columns.tolist()}")
        print(f"\nSample:")
        print(chain_df.head())
        
        # Check low yield
        low_yield = chain_df[chain_df['total_yield_pct'] < 85]
        print(f"\nLow yield chains (<85%): {len(low_yield)}")
    else:
        print("Table is EMPTY!")
        
finally:
    db.close()
