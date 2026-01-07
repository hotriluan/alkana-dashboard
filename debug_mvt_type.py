import pandas as pd

mb51 = pd.read_excel('demodata/mb51.XLSX')
batch = '25L2502310'

# Get all rows for this batch
m = mb51[mb51['Batch'] == batch].copy()

print(f"All movements for batch {batch}:")
print(f"Total: {len(m)} rows\n")

# Check Movement Type values
print("Movement Type values and types:")
for idx, row in m.head(10).iterrows():
    mvt = row['Movement Type']
    plant = row['Plant']
    sloc = row['Storage Location']
    date = row['Posting Date']
    print(f"  MVT: '{mvt}' (type: {type(mvt).__name__}) | Plant: {plant} | SLoc: {sloc} | Date: {date}")

# Check specifically for '101' as string
print("\n\nChecking for Movement Type == '101' (string):")
m_101_str = m[m['Movement Type'] == '101']
print(f"Found: {len(m_101_str)} rows")

# Check for Movement Type == 101 (int)
print("\nChecking for Movement Type == 101 (int):")
m_101_int = m[m['Movement Type'] == 101]
print(f"Found: {len(m_101_int)} rows")

# Check with Plant 1401
print("\n\nWith Plant 1401:")
m_1401 = m[m['Plant'] == 1401]
print(f"Total at Plant 1401: {len(m_1401)} rows")
for idx, row in m_1401.head(5).iterrows():
    print(f"  MVT: '{row['Movement Type']}' | Date: {row['Posting Date']}")

# Try to find the specific row from the image
print("\n\nLooking for MVT='101' AND Plant=1401:")
m_target = m[(m['Movement Type'] == '101') & (m['Plant'] == 1401)]
print(f"Found: {len(m_target)} rows")
if not m_target.empty:
    print(m_target[['Posting Date', 'Movement Type', 'Plant', 'Storage Location']])
