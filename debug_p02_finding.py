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
    
    # Create transformer
    transformer = Transformer(db)
    transformer.build_uom_conversion()
    
    # Create tracker
    tracker = YieldTracker(cooispi_df, mb51_df, transformer.uom_converter)
    
    # Test with first P01
    p01_orders = tracker.find_p01_orders()
    first_p01 = p01_orders.iloc[0]
    
    print(f"=== TESTING P01: {first_p01['order']} ===")
    print(f"Batch: {first_p01['batch']}")
    print(f"Material: {first_p01['material']}")
    
    # Find input batches (P02)
    p02_batches = tracker.find_input_batches(first_p01['order'])
    
    print(f"\n=== P02 BATCHES CONSUMED ===")
    print(f"Found: {len(p02_batches) if p02_batches else 0} batches")
    
    if p02_batches:
        print(f"P02 batches: {p02_batches}")
        
        # Check if these are actually P02
        for p02_batch in p02_batches:
            p02_order = tracker.find_order_by_batch(p02_batch, 'P02')
            if p02_order is not None:
                print(f"  ✓ {p02_batch} → P02 Order: {p02_order['order']}")
            else:
                print(f"  ✗ {p02_batch} → NOT P02")
    else:
        print("NO P02 batches found!")
        
        # Debug: Check MB51 for MVT 261 (consumption)
        print("\n=== CHECKING MB51 FOR CONSUMPTION ===")
        consumption = mb51_df[
            (mb51_df['col_1_mvt_type'] == 261) &
            (mb51_df['col_12_reference'] == first_p01['order'])
        ]
        print(f"MVT 261 records for order {first_p01['order']}: {len(consumption)}")
        
        if not consumption.empty:
            print("\nSample consumption:")
            print(consumption[['col_0_posting_date', 'col_1_mvt_type', 'col_6_batch', 'col_4_material', 'col_12_reference']].head())
        
finally:
    db.close()
