from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    cooispi_df = pd.read_sql_table('raw_cooispi', db.bind)
    
    # Get a P02 batch that appears in MVT 261
    p02_batch = '25L2494510'
    
    print(f"=== ANALYZING P02 BATCH: {p02_batch} ===\n")
    
    # Find this batch in COOISPI
    p02_order = cooispi_df[cooispi_df['batch'] == p02_batch]
    if not p02_order.empty:
        print("P02 Order Info:")
        print(f"  Order: {p02_order.iloc[0]['order']}")
        print(f"  MRP: {p02_order.iloc[0]['mrp_controller']}")
        print(f"  Material: {p02_order.iloc[0]['material_number']}")
    
    # Find MVT 261 for this P02 batch
    mvt_261_p02 = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_6_batch'] == p02_batch)
    ]
    
    print(f"\nMVT 261 for this P02 batch:")
    print(f"  Records: {len(mvt_261_p02)}")
    
    if not mvt_261_p02.empty:
        mat_doc = mvt_261_p02.iloc[0]['col_11_material_doc']
        print(f"  Material Doc: {mat_doc}")
        print(f"  Reference: {mvt_261_p02.iloc[0]['col_12_reference']}")
        
        # Find ALL MVT 261 with same material_doc
        print(f"\n=== ALL MVT 261 WITH SAME MATERIAL_DOC: {mat_doc} ===")
        same_doc = mb51_df[
            (mb51_df['col_1_mvt_type'] == 261) &
            (mb51_df['col_11_material_doc'] == mat_doc)
        ]
        
        print(f"Total records: {len(same_doc)}")
        print("\nBatches in this material doc:")
        for batch in same_doc['col_6_batch'].unique():
            # Check if this is P02 or P03
            order_info = cooispi_df[cooispi_df['batch'] == batch]
            if not order_info.empty:
                mrp = order_info.iloc[0]['mrp_controller']
                order_num = order_info.iloc[0]['order']
                print(f"  {batch} → {mrp} Order: {order_num}")
            else:
                print(f"  {batch} → NOT in COOISPI")
        
        # Check if there's a MVT 101 (GR) with same material_doc
        # This would be the OUTPUT (P01 batch)
        print(f"\n=== CHECKING MVT 101 (GR) WITH SAME MATERIAL_DOC ===")
        mvt_101 = mb51_df[
            (mb51_df['col_1_mvt_type'] == 101) &
            (mb51_df['col_11_material_doc'] == mat_doc)
        ]
        
        print(f"MVT 101 records: {len(mvt_101)}")
        if not mvt_101.empty:
            for idx, row in mvt_101.iterrows():
                batch_101 = row['col_6_batch']
                # Check if this is P01
                order_info = cooispi_df[cooispi_df['batch'] == batch_101]
                if not order_info.empty:
                    mrp = order_info.iloc[0]['mrp_controller']
                    order_num = order_info.iloc[0]['order']
                    print(f"  {batch_101} → {mrp} Order: {order_num} ✓ OUTPUT!")
                else:
                    print(f"  {batch_101} → NOT in COOISPI")
        
finally:
    db.close()
