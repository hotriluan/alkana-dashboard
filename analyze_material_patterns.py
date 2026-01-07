from src.db.connection import SessionLocal
import pandas as pd
from datetime import timedelta

db = SessionLocal()

try:
    mb51_df = pd.read_sql_table('raw_mb51', db.bind)
    
    print("=== MATERIAL NAME PATTERN ANALYSIS ===\n")
    
    # Get P02 consumption transactions (MVT 261 @ 1201)
    p02_consumption = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_2_plant'] == 1201)
    ].copy()
    
    # Get P01 production transactions (MVT 101 @ 1401)
    p01_production = mb51_df[
        (mb51_df['col_1_mvt_type'] == 101) &
        (mb51_df['col_2_plant'] == 1401)
    ].copy()
    
    print(f"P02 Consumption transactions: {len(p02_consumption)}")
    print(f"P01 Production transactions: {len(p01_production)}")
    
    # Analyze material name patterns
    print("\n=== SAMPLE P02 MATERIALS ===")
    p02_materials = p02_consumption['col_5_material_desc'].value_counts().head(10)
    for material, count in p02_materials.items():
        print(f"{material}: {count} transactions")
    
    print("\n=== SAMPLE P01 MATERIALS ===")
    p01_materials = p01_production['col_5_material_desc'].value_counts().head(10)
    for material, count in p01_materials.items():
        print(f"{material}: {count} transactions")
    
    # Check suffix patterns
    print("\n=== CHECKING SUFFIX PATTERNS ===")
    
    # Extract unique P01 materials
    p01_unique = p01_production['col_5_material_desc'].unique()
    
    # Common suffixes
    suffixes = ['-4L', '-1L', '-6K', '-20K', '-18K', '-5L']
    
    suffix_counts = {}
    for suffix in suffixes:
        count = sum(1 for mat in p01_unique if mat and suffix in mat)
        suffix_counts[suffix] = count
    
    print("P01 Material Suffix Distribution:")
    for suffix, count in sorted(suffix_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {suffix}: {count} materials")
    
    # Try to match P02→P01 by removing suffix
    print("\n=== TESTING MATERIAL MATCHING ===")
    
    # Sample: Take first 5 P02 materials
    sample_p02 = p02_consumption.head(20)
    
    matches_found = 0
    for idx, p02_row in sample_p02.iterrows():
        p02_mat = p02_row['col_5_material_desc']
        p02_date = p02_row['col_0_posting_date']
        p02_qty = abs(p02_row['col_7_qty'])
        
        # Try to find matching P01 (with suffix)
        for suffix in suffixes:
            p01_mat_expected = f"{p02_mat}{suffix}"
            
            # Find P01 with this material name
            p01_match = p01_production[
                p01_production['col_5_material_desc'] == p01_mat_expected
            ]
            
            if not p01_match.empty:
                # Check date proximity (within 7 days)
                p01_match['date_diff'] = abs(
                    (pd.to_datetime(p01_match['col_0_posting_date']) - 
                     pd.to_datetime(p02_date)).dt.days
                )
                
                close_dates = p01_match[p01_match['date_diff'] <= 7]
                
                if not close_dates.empty:
                    p01_row = close_dates.iloc[0]
                    p01_qty = p01_row['col_7_qty']
                    p01_uom = p01_row['col_8_uom']
                    date_diff = p01_row['date_diff']
                    
                    print(f"\n✓ MATCH FOUND:")
                    print(f"  P02: {p02_mat}")
                    print(f"    Date: {p02_date}, Qty: {p02_qty} KG")
                    print(f"  P01: {p01_mat_expected}")
                    print(f"    Date: {p01_row['col_0_posting_date']}, Qty: {p01_qty} {p01_uom}")
                    print(f"    Date diff: {date_diff} days")
                    
                    matches_found += 1
                    break
    
    print(f"\n=== SUMMARY ===")
    print(f"Tested: 20 P02 transactions")
    print(f"Matches found: {matches_found}")
    print(f"Match rate: {matches_found/20*100:.1f}%")
    
finally:
    db.close()
