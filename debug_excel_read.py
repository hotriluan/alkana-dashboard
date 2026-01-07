import pandas as pd

# Read with different methods
print("Method 1: Default read_excel")
mb51 = pd.read_excel('demodata/mb51.XLSX')
print(f"Total rows: {len(mb51)}")
print(f"Columns: {mb51.columns.tolist()[:5]}")

# Check batch 25L2502310
batch = '25L2502310'
m = mb51[mb51['Batch'] == batch]
print(f"\nRows with batch {batch}: {len(m)}")

# Check with MVT 101 and Plant 1401
m_101_1401 = mb51[(mb51['Batch'] == batch) & (mb51['Movement Type'] == 101) & (mb51['Plant'] == 1401)]
print(f"Rows with MVT 101 @ Plant 1401: {len(m_101_1401)}")

if not m_101_1401.empty:
    print("\nFound it!")
    print(m_101_1401[['Posting Date', 'Movement Type', 'Plant', 'Storage Location', 'Batch']])
else:
    print("\nNOT FOUND - checking data types...")
    print(f"Batch column dtype: {mb51['Batch'].dtype}")
    print(f"Movement Type dtype: {mb51['Movement Type'].dtype}")
    print(f"Plant dtype: {mb51['Plant'].dtype}")
    
    # Check unique values
    print(f"\nUnique batches containing '2502310': {mb51[mb51['Batch'].astype(str).str.contains('2502310', na=False)]['Batch'].unique()}")
    
    # Try with string comparison
    m_str = mb51[(mb51['Batch'].astype(str) == batch) & (mb51['Movement Type'] == 101) & (mb51['Plant'] == 1401)]
    print(f"\nWith string comparison: {len(m_str)} rows")
    if not m_str.empty:
        print(m_str[['Posting Date', 'Movement Type', 'Plant', 'Batch']])
