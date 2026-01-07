
import pandas as pd
import os

# Paths
FILES = {
    'mb51': r'c:\dev\alkana-dashboard\demodata\mb51.xlsx',
    'cooispi': r'c:\dev\alkana-dashboard\demodata\cooispi.xlsx',
    'zrmm024': r'c:\dev\alkana-dashboard\demodata\zrmm024.xlsx'
}
OUTPUT_FILE = r'c:\dev\alkana-dashboard\demodata\consolidated_orders.xlsx'

def main():
    print("Starting consolidation...")
    
    # --- Step 1: MB51 ---
    print("Reading MB51...")
    # MB51 indices: Mvt=1, Batch=6, PO=15
    mb51 = pd.read_excel(FILES['mb51'], header=None)
    mb51 = mb51.rename(columns={1: 'Movement Type', 6: 'Batch', 15: 'Purchase Order'})
    
    # Filter: PO starts with '44' AND Mvt is 101
    # Ensure PO is string, handle NaNs
    mb51['Purchase Order'] = mb51['Purchase Order'].astype(str).str.replace(r'\.0$', '', regex=True)
    mb51['Movement Type'] = pd.to_numeric(mb51['Movement Type'], errors='coerce')
    
    print(f"MB51 Total Rows: {len(mb51)}")
    
    mb51_filtered = mb51[
        (mb51['Purchase Order'].str.startswith('44')) & 
        (mb51['Movement Type'] == 101)
    ].copy()
    
    print(f"MB51 Filtered Rows (PO='44*', Mvt=101): {len(mb51_filtered)}")
    
    # Prepare for join: Keep Batch and PO. Drop duplicates to avoid exploding the join if multiple lines exist for same batch/PO
    # If a batch has multiple POs, this simple logic might be ambiguous, but usually 1:1 for 101.
    mb51_join = mb51_filtered[['Batch', 'Purchase Order']].drop_duplicates(subset=['Batch'])
    print(f"MB51 Unique Batches for Join: {len(mb51_join)}")
    
    # --- Step 2: COOISPI ---
    print("\nReading COOISPI...")
    cooispi = pd.read_excel(FILES['cooispi']) # Has headers
    
    # Filter: Sales Order has value
    cooispi_filtered = cooispi[cooispi['Sales Order'].notna() & (cooispi['Sales Order'].astype(str) != 'nan')]
    print(f"COOISPI Filtered Rows (Sales Order exists): {len(cooispi_filtered)}")
    
    # Join with MB51 on Batch
    # COOISPI has 'Batch' column.
    # Ensure Batch types match (string)
    cooispi_filtered['Batch'] = cooispi_filtered['Batch'].astype(str)
    mb51_join['Batch'] = mb51_join['Batch'].astype(str)
    
    merged_step2 = pd.merge(
        cooispi_filtered, 
        mb51_join, 
        on='Batch', 
        how='left' 
        # Requirement: "Add a column ... value from MB51 ... key is Batch". 
        # Assuming we keep all COOISPI filtered rows.
    )
    
    # --- Step 3: ZRMM024 ---
    print("\nReading ZRMM024...")
    # ZRMM024 indices: PO=0, Date=2
    zrmm = pd.read_excel(FILES['zrmm024'], header=None)
    zrmm = zrmm.rename(columns={0: 'Purchase Order', 2: 'Purchase Order Date'})
    
    # Clean PO for join
    zrmm['Purchase Order'] = zrmm['Purchase Order'].astype(str).str.replace(r'\.0$', '', regex=True)
    
    # Unique POs for join
    zrmm_join = zrmm[['Purchase Order', 'Purchase Order Date']].drop_duplicates(subset=['Purchase Order'])
    
    # Join Step 2 result with ZRMM024 on Purchase Order
    final_df = pd.merge(
        merged_step2,
        zrmm_join,
        on='Purchase Order',
        how='left'
    )
    
    # --- Step 4: Export ---
    print(f"\nSaving to {OUTPUT_FILE}...")
    final_df.to_excel(OUTPUT_FILE, index=False)
    print("Done.")
    
    # Verify a few rows
    print("\nSample Output:")
    print(final_df[['Order', 'Sales Order', 'Batch', 'Purchase Order', 'Purchase Order Date']].head())
    print(f"Total Result Rows: {len(final_df)}")
    print(f"Rows with Populated PO: {final_df['Purchase Order'].notna().sum()}")

if __name__ == "__main__":
    main()
