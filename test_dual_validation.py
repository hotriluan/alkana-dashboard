from src.db.connection import SessionLocal
import pandas as pd

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    
    print("=== TESTING BATCH + MATERIAL NAME VALIDATION ===\n")
    
    def get_p01_batch_from_p02(p02_batch):
        """Convert P02 batch to P01 batch"""
        if not p02_batch or len(p02_batch) < 10:
            return None
        
        try:
            prefix = p02_batch[:6]
            two_digits = int(p02_batch[6:8])
            suffix = p02_batch[8:]
            
            p01_two_digits = two_digits - 1
            p01_batch = f"{prefix}{p01_two_digits:02d}{suffix}"
            
            return p01_batch
        except:
            return None
    
    def validate_material_names(p02_material, p01_material):
        """
        Validate that P01 material name = P02 material name + suffix
        
        Examples:
        - P02: "PFT-215 LIGHT GREY VN"
        - P01: "PFT-215 LIGHT GREY VN-18KP" ✓
        
        Returns: True if valid, False otherwise
        """
        if not p02_material or not p01_material:
            return False
        
        # P01 should start with P02 name
        if not p01_material.startswith(p02_material):
            return False
        
        # P01 should have suffix after P02 name
        suffix = p01_material[len(p02_material):]
        
        # Suffix should start with hyphen and contain packaging info
        if not suffix or not suffix.startswith('-'):
            return False
        
        return True
    
    # Test with all P02 batches
    print("=== TESTING WITH DUAL VALIDATION ===\n")
    
    p02_txns = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_2_plant'] == 1201)
    ].copy()
    
    p02_batches = p02_txns['col_6_batch'].unique()
    
    batch_matches = 0
    material_matches = 0
    both_matches = 0
    
    valid_pairs = []
    
    for p02_batch in p02_batches[:100]:  # Test first 100
        if not p02_batch:
            continue
        
        # Get P01 batch
        p01_batch = get_p01_batch_from_p02(p02_batch)
        if not p01_batch:
            continue
        
        # Get P02 details
        p02_detail = p02_txns[p02_txns['col_6_batch'] == p02_batch].iloc[0]
        p02_material = p02_detail['col_5_material_desc']
        
        # Check if P01 exists
        p01_txn = mb51_df[
            (mb51_df['col_6_batch'] == p01_batch) &
            (mb51_df['col_1_mvt_type'] == 101) &
            (mb51_df['col_2_plant'] == 1401)
        ]
        
        if not p01_txn.empty:
            batch_matches += 1
            
            # Get P01 material
            p01_material = p01_txn.iloc[0]['col_5_material_desc']
            
            # Validate material names
            if validate_material_names(p02_material, p01_material):
                material_matches += 1
                both_matches += 1
                
                valid_pairs.append({
                    'p02_batch': p02_batch,
                    'p01_batch': p01_batch,
                    'p02_material': p02_material,
                    'p01_material': p01_material,
                    'p02_qty': abs(p02_detail['col_7_qty']),
                    'p01_qty': p01_txn.iloc[0]['col_7_qty'],
                    'p01_uom': p01_txn.iloc[0]['col_8_uom']
                })
                
                if both_matches <= 10:  # Show first 10
                    print(f"✓ Valid Pair #{both_matches}:")
                    print(f"  P02 Batch: {p02_batch}")
                    print(f"    Material: {p02_material}")
                    print(f"    Qty: {abs(p02_detail['col_7_qty'])} KG")
                    print(f"  P01 Batch: {p01_batch}")
                    print(f"    Material: {p01_material}")
                    print(f"    Qty: {p01_txn.iloc[0]['col_7_qty']} {p01_txn.iloc[0]['col_8_uom']}")
                    print()
            else:
                # Material name doesn't match
                if batch_matches - material_matches <= 5:  # Show first 5 mismatches
                    print(f"✗ Material Mismatch:")
                    print(f"  Batch: {p02_batch} → {p01_batch}")
                    print(f"  P02: {p02_material}")
                    print(f"  P01: {p01_material}")
                    print()
    
    print(f"\n=== RESULTS (First 100 P02 batches) ===")
    print(f"Batch matches: {batch_matches}")
    print(f"Material name matches: {material_matches}")
    print(f"Both validations passed: {both_matches}")
    print(f"Match rate (batch only): {batch_matches/100*100:.1f}%")
    print(f"Match rate (both): {both_matches/100*100:.1f}%")
    
    # Test full dataset
    print(f"\n=== TESTING FULL DATASET ===")
    
    total_batch_matches = 0
    total_both_matches = 0
    total_tested = 0
    
    for p02_batch in p02_batches:
        if not p02_batch:
            continue
        
        total_tested += 1
        
        p01_batch = get_p01_batch_from_p02(p02_batch)
        if not p01_batch:
            continue
        
        # Get P02 material
        p02_detail = p02_txns[p02_txns['col_6_batch'] == p02_batch].iloc[0]
        p02_material = p02_detail['col_5_material_desc']
        
        # Check P01
        p01_txn = mb51_df[
            (mb51_df['col_6_batch'] == p01_batch) &
            (mb51_df['col_1_mvt_type'] == 101) &
            (mb51_df['col_2_plant'] == 1401)
        ]
        
        if not p01_txn.empty:
            total_batch_matches += 1
            
            p01_material = p01_txn.iloc[0]['col_5_material_desc']
            
            if validate_material_names(p02_material, p01_material):
                total_both_matches += 1
    
    print(f"Total P02 batches: {total_tested}")
    print(f"Batch matches: {total_batch_matches} ({total_batch_matches/total_tested*100:.1f}%)")
    print(f"Both validations: {total_both_matches} ({total_both_matches/total_tested*100:.1f}%)")
    
    print(f"\n=== IMPROVEMENT ===")
    print(f"Batch-only approach: {total_batch_matches/total_tested*100:.1f}%")
    print(f"Batch + Material validation: {total_both_matches/total_tested*100:.1f}%")
    print(f"False positives eliminated: {total_batch_matches - total_both_matches}")
    
finally:
    db.close()
