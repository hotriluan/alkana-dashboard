import pandas as pd

mb51 = pd.read_excel('demodata/mb51.XLSX')
batch = '25L2502310'

print(f"All MB51 movements for batch {batch}:\n")
m = mb51[mb51['Batch'] == batch].copy()
if not m.empty:
    m['Posting Date'] = pd.to_datetime(m['Posting Date'])
    m = m.sort_values('Posting Date')
    for _, row in m.iterrows():
        mvt = int(row['Movement Type']) if pd.notna(row['Movement Type']) else 0
        print(f"{row['Posting Date']} | MVT {mvt:3d} | Plant {row['Plant']} | SLoc {row['Storage Location']}")
else:
    print("NO movements found!")
