
import pandas as pd
import os

# Configuration
FILES = {
    'cooispi': r'c:\dev\alkana-dashboard\demodata\cooispi.xlsx',
    'mb51': r'c:\dev\alkana-dashboard\demodata\mb51.xlsx',
    'zrmm024': r'c:\dev\alkana-dashboard\demodata\zrmm024.xlsx'
}

# Column Indices (0-based) for files without headers
# Based on inspection of converted Markdown files
MB51_COLS = {
    'Material': 4,
    'Plant': 2,
    'SalesOrder': 13, # Inferred from finding sales order numbers in column Unnamed: 13
    'MoveType': 1,
    'Qty': 7
}

ZRMM024_COLS = {
    'Material': 5, # Inferred
    'Plant': 3,    # Inferred (1201)
    'Strategy': -2 # Inferred (MTO/MTS is 2nd to last column)
}

def load_data():
    print("Loading data...")
    dfs = {}
    
    # Load COOISPI (Has headers)
    print(f"Reading {FILES['cooispi']}...")
    dfs['cooispi'] = pd.read_excel(FILES['cooispi'])
    
    # Load MB51 (No headers found)
    print(f"Reading {FILES['mb51']}...")
    try:
        # Read with header=None
        df = pd.read_excel(FILES['mb51'], header=None)
        # Rename columns for easier access
        df = df.rename(columns={
            MB51_COLS['Material']: 'Material',
            MB51_COLS['Plant']: 'Plant',
            MB51_COLS['SalesOrder']: 'Sales Order',
            MB51_COLS['MoveType']: 'Movement Type',
            MB51_COLS['Qty']: 'Quantity'
        })
        dfs['mb51'] = df
    except Exception as e:
        print(f"Error reading MB51: {e}")

    # Load ZRMM024 (No headers found)
    print(f"Reading {FILES['zrmm024']}...")
    try:
        df = pd.read_excel(FILES['zrmm024'], header=None)
        # Rename columns
        # Handle negative index for Strategy by calculating positive index
        strategy_idx = df.shape[1] + ZRMM024_COLS['Strategy']
        df = df.rename(columns={
            ZRMM024_COLS['Material']: 'Material',
            ZRMM024_COLS['Plant']: 'Plant',
            strategy_idx: 'Strategy'
        })
        dfs['zrmm024'] = df
    except Exception as e:
        print(f"Error reading ZRMM024: {e}")
        
    return dfs

def verify_mto(dfs):
    print("\n--- Verifying MTO Logic ---")
    
    # 1. Identify MTO Materials from ZRMM024
    zrmm = dfs.get('zrmm024')
    if zrmm is None:
        print("ZRMM024 not loaded, skipping.")
        return

    # Filter for MTO
    # Ensure Strategy column is string and clean
    zrmm['Strategy'] = zrmm['Strategy'].astype(str).str.strip()
    mto_items = zrmm[zrmm['Strategy'] == 'MTO']
    
    mto_materials = set(mto_items['Material'].unique())
    print(f"Found {len(mto_materials)} unique MTO materials in ZRMM024.")
    
    if len(mto_materials) == 0:
        print("No MTO materials found (maybe Strategy column index is wrong?). Checking unique values in Strategy column:")
        print(zrmm['Strategy'].unique())
        return

    # 2. Check COOISPI
    cooispi = dfs.get('cooispi')
    if cooispi is not None:
        print("\nChecking COOISPI (Production Orders)...")
        # Ensure Material Number is string for matching (remove .0 if float)
        # Often Excel reads '1000' as 1000 (int) or 1000.0 (float).
        # We need to standardize.
        
        # Helper to normalize material
        def norm_mat(x):
            try:
                return str(int(x)) if pd.notnull(x) else str(x)
            except:
                return str(x)

        cooispi['Material Number'] = cooispi['Material Number'].apply(norm_mat)
        mto_materials_str = {norm_mat(m) for m in mto_materials}
        
        # Filter COOISPI for MTO materials
        mto_orders = cooispi[cooispi['Material Number'].isin(mto_materials_str)]
        print(f"Found {len(mto_orders)} production orders for MTO materials.")
        
        # Check if Sales Order is present
        # Sales Order column might be NaN for non-linked orders
        # In MTO, it MUST be linked.
        
        missing_so = mto_orders[mto_orders['Sales Order'].isna() | (mto_orders['Sales Order'] == 'nan')]
        if not missing_so.empty:
            print(f"WARNING: Found {len(missing_so)} orders for MTO materials MISSING Sales Order assignment!")
            print(missing_so[['Order', 'Material Number', 'Sales Order']].head())
        else:
            print("SUCCESS: All MTO production orders have Sales Order assignment.")

    # 3. Check MB51
    mb51 = dfs.get('mb51')
    if mb51 is not None:
        print("\nChecking MB51 (Material Movements)...")
        mb51['Material'] = mb51['Material'].apply(norm_mat)
        
        mto_moves = mb51[mb51['Material'].isin(mto_materials_str)]
        print(f"Found {len(mto_moves)} movements for MTO materials.")
        
        # Check Sales Order (Index 13)
        # Note: Not all movements (like 101, 261) might strictly require SO on the document item itself if valid at header,
        # but for Special Stock E, it should be there.
        # We'll just check if it's populated.
        
        # 'Sales Order' column might be numeric or string.
        missing_so_moves = mto_moves[mto_moves['Sales Order'].isna()]
        
        if not missing_so_moves.empty:
            print(f"WARNING: Found {len(missing_so_moves)} movements for MTO materials without Sales Order reference.")
            # This might be valid for some movement types or scenarios, but flagging it is good.
            print(missing_so_moves[['Material', 'Movement Type', 'Sales Order']].head())
        else:
            print("SUCCESS: All MTO movements have Sales Order reference.")

if __name__ == "__main__":
    dfs = load_data()
    verify_mto(dfs)
