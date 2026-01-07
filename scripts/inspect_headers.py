
import pandas as pd
import glob
import os

files = [
    r'c:\dev\alkana-dashboard\demodata\mb51.xlsx',
    r'c:\dev\alkana-dashboard\demodata\zrmm024.xlsx',
    r'c:\dev\alkana-dashboard\demodata\cooispi.xlsx'
]

for f in files:
    print(f"--- Inspecting {os.path.basename(f)} ---")
    try:
        # Read first 10 rows without header
        df = pd.read_excel(f, header=None, nrows=10)
        print(df.to_string())
    except Exception as e:
        print(f"Error reading {f}: {e}")
    print("\n")
