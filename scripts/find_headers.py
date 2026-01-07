
import pandas as pd
import os

files_keywords = {
    r'c:\dev\alkana-dashboard\demodata\mb51.xlsx': ['Material', 'Plant', 'Movement type', 'Posting Date'],
    r'c:\dev\alkana-dashboard\demodata\zrmm024.xlsx': ['Material', 'Plant', 'MRP controller', 'Exception'],
    r'c:\dev\alkana-dashboard\demodata\cooispi.xlsx': ['Order', 'Material', 'Plant']
}

for f, keywords in files_keywords.items():
    print(f"--- Analyzing {os.path.basename(f)} ---")
    try:
        df = pd.read_excel(f, header=None, nrows=20)
        header_row = -1
        for i, row in df.iterrows():
            row_str = row.astype(str).str.lower().tolist()
            # Check if at least 2 keywords are in the row
            matches = sum(any(k.lower() in str(cell).lower() for cell in row_str) for k in keywords)
            if matches >= 2:
                header_row = i
                print(f"Found header at row {i}: {row.tolist()}")
                break
        
        if header_row == -1:
            print("Could not find header row.")
        else:
            # Print columns found
            pass
            
    except Exception as e:
        print(f"Error: {e}")
    print("\n")
