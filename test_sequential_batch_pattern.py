from src.db.connection import SessionLocal
import pandas as pd
import re

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    
    print("=== TESTING SEQUENTIAL BATCH NUMBER PATTERN ===\n")
    
    def get_p01_batch_from_p02(p02_batch):
        """
        Convert P02 batch to P01 batch by decrementing digit at position 7-8
        
        Example: 25L2476310 → 25L2476210
                      ^^           ^^
                      63           62
        """
        if not p02_batch or len(p02_batch) < 10:
            return None
        
        # Extract the two digits at position 7-8 (0-indexed: 6-7)
        try:
            prefix = p02_batch[:6]  # '25L247'
            two_digits = int(p02_batch[6:8])  # '63'
            suffix = p02_batch[8:]  # '10'
            
            # Decrement
            p01_two_digits = two_digits - 1
            
            # Reconstruct
            p01_batch = f"{prefix}{p01_two_digits:02d}{suffix}"
            
            return p01_batch
        except:
            return None
    
    # Test with user's example
    test_p02 = '25L2476310'
    test_p01_expected = '25L2476210'
    test_p01_calculated = get_p01_batch_from_p02(test_p02)
    
    print(f"Test Case:")
    print(f"  P02 Batch: {test_p02}")
    print(f"  Expected P01: {test_p01_expected}")
    print(f"  Calculated P01: {test_p01_calculated}")
    print(f"  Match: {test_p01_calculated == test_p01_expected} ✓\n")
    
    # Now test with all P02 batches
    print("=== TESTING ALL P02 BATCHES ===\n")
    
    # Get P02 consumption transactions
    p02_txns = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_2_plant'] == 1201)
    ].copy()
    
    # Get unique P02 batches
    p02_batches = p02_txns['col_6_batch'].unique()
    
    print(f"Total P02 batches: {len(p02_batches)}")
    
    # Test pattern
    matches = 0
    mismatches = 0
    
    for p02_batch in p02_batches[:50]:  # Test first 50
        if not p02_batch:
            continue
            
        p01_batch_expected = get_p01_batch_from_p02(p02_batch)
        
        if not p01_batch_expected:
            continue
        
        # Check if this P01 batch exists in MB51
        p01_exists = mb51_df[
            (mb51_df['col_6_batch'] == p01_batch_expected) &
            (mb51_df['col_1_mvt_type'] == 101) &
            (mb51_df['col_2_plant'] == 1401)
        ]
        
        if not p01_exists.empty:
            matches += 1
            
            # Get details
            p02_detail = p02_txns[p02_txns['col_6_batch'] == p02_batch].iloc[0]
            p01_detail = p01_exists.iloc[0]
            
            p02_qty = abs(p02_detail['col_7_qty'])
            p01_qty = p01_detail['col_7_qty']
            p01_uom = p01_detail['col_8_uom']
            
            if matches <= 5:  # Show first 5 matches
                print(f"\n✓ Match #{matches}:")
                print(f"  P02 Batch: {p02_batch}")
                print(f"    Material: {p02_detail['col_5_material_desc']}")
                print(f"    Qty: {p02_qty} KG")
                print(f"  P01 Batch: {p01_batch_expected}")
                print(f"    Material: {p01_detail['col_5_material_desc']}")
                print(f"    Qty: {p01_qty} {p01_uom}")
        else:
            mismatches += 1
    
    print(f"\n=== RESULTS (First 50 P02 batches) ===")
    print(f"Matches: {matches}")
    print(f"Mismatches: {mismatches}")
    print(f"Match Rate: {matches/(matches+mismatches)*100:.1f}%")
    
    # Test full dataset
    print(f"\n=== TESTING FULL DATASET ===")
    
    total_matches = 0
    total_tested = 0
    
    for p02_batch in p02_batches:
        if not p02_batch:
            continue
            
        p01_batch_expected = get_p01_batch_from_p02(p02_batch)
        
        if not p01_batch_expected:
            continue
        
        total_tested += 1
        
        # Check if P01 exists
        p01_exists = mb51_df[
            (mb51_df['col_6_batch'] == p01_batch_expected) &
            (mb51_df['col_1_mvt_type'] == 101) &
            (mb51_df['col_2_plant'] == 1401)
        ]
        
        if not p01_exists.empty:
            total_matches += 1
    
    print(f"Total P02 batches tested: {total_tested}")
    print(f"Total matches found: {total_matches}")
    print(f"Overall Match Rate: {total_matches/total_tested*100:.1f}%")
    
finally:
    db.close()
