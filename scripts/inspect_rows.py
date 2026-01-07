
import pandas as pd
import os

files = [
    r'c:\dev\alkana-dashboard\demodata\mb51.xlsx',
    r'c:\dev\alkana-dashboard\demodata\zrmm024.xlsx'
]

def print_rows():
    for f in files:
        print(f"\n--- {os.path.basename(f)} ---")
        try:
            df = pd.read_excel(f, header=None, nrows=5)
            # Print with index to help counting
            for i, row in df.iterrows():
                print(f"Row {i}:")
                for col_idx, val in enumerate(row):
                    print(f"  Col {col_idx}: {val}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print_rows()
