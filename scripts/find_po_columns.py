
import pandas as pd
import os

files = {
    'mb51': r'c:\dev\alkana-dashboard\demodata\mb51.xlsx',
    'zrmm024': r'c:\dev\alkana-dashboard\demodata\zrmm024.xlsx'
}

def inspect_columns():
    for name, path in files.items():
        print(f"\n--- Inspecting {name} ({os.path.basename(path)}) ---")
        try:
            # Read first 100 rows to find patterns
            df = pd.read_excel(path, header=None, nrows=100)
            
            # Look for values starting with '44' (string) which might be POs
            # Look for dates
            
            print("Row 0 (Sample):")
            print(df.iloc[0].tolist())
            
            print("\nScanning columns for '44...' values:")
            for col in df.columns:
                # Convert to string and check
                sample = df[col].astype(str).str.strip()
                matches = sample[sample.str.startswith('44', na=False)]
                if not matches.empty:
                    print(f"Column {col}: Found {len(matches)} matches (e.g. {matches.iloc[0]})")
                    
            print("\nScanning columns for Batches (likely string/alphanumeric):")
            # In MB51 batch is often 10 digits/chars.
            # We know from previous view that Batch was likely col 6 in MB51 (index 6 in 0-based? or 7?)
            # Let's check column indices specifically.
            
        except Exception as e:
            print(f"Error reading {name}: {e}")

if __name__ == "__main__":
    inspect_columns()
