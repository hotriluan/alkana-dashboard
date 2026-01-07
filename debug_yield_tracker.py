from src.db.connection import SessionLocal
from src.db.models import RawCooispi, RawMb51
from src.core.yield_tracker import YieldTracker
from src.etl.transform import Transformer
import pandas as pd

db = SessionLocal()

try:
    # Load data
    cooispi_df = pd.read_sql_table('raw_cooispi', db.bind)
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    
    print(f"=== DATA LOADED ===")
    print(f"COOISPI: {len(cooispi_df)} records")
    print(f"MB51: {len(mb51_df)} records")
    
    # Create transformer to get UOM converter
    transformer = Transformer(db)
    transformer.build_uom_conversion()
    uom_converter = transformer.uom_converter
    
    # Create tracker
    tracker = YieldTracker(cooispi_df, mb51_df, uom_converter)
    
    # Find P01 orders
    p01_orders = tracker.find_p01_orders()
    
    print(f"\n=== P01 ORDERS ===")
    print(f"Total P01 orders: {len(p01_orders)}")
    
    if not p01_orders.empty:
        print(f"\nSample P01 orders:")
        print(p01_orders[['order', 'batch', 'material', 'mrp_controller']].head(10))
        
        # Try building chain for first P01
        first_p01 = p01_orders.iloc[0]
        print(f"\n=== TESTING CHAIN BUILD ===")
        print(f"P01 Order: {first_p01['order']}")
        
        chain = tracker.build_chain_from_p01(first_p01['order'])
        
        if chain:
            print(f"Chain Complete: {chain.chain_complete}")
            print(f"Total Yield: {chain.total_yield_pct}%")
            if chain.p01:
                print(f"P01: {chain.p01.order} - {chain.p01.batch}")
            if chain.p02:
                print(f"P02: {chain.p02.order} - {chain.p02.batch}")
            if chain.p03:
                print(f"P03: {chain.p03.order} - {chain.p03.batch}")
        else:
            print("Chain is None!")
    else:
        print("NO P01 ORDERS FOUND!")
        print("\nChecking MRP controllers in data:")
        if 'mrp_controller' in tracker.orders.columns:
            print(tracker.orders['mrp_controller'].value_counts())
        else:
            print("mrp_controller column NOT FOUND in orders!")
            print(f"Available columns: {tracker.orders.columns.tolist()}")
        
finally:
    db.close()
