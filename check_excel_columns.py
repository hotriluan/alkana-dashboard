import pandas as pd
from pathlib import Path

file_path = Path('demodata/zrsd004.XLSX')

# Read Excel headers only
df = pd.read_excel(file_path, nrows=0)

print('📋 EXACT COLUMN NAMES IN EXCEL HEADER:')
for i, col in enumerate(df.columns):
    print(f'  [{i:2d}] "{col}"')

print(f'\n✅ Total columns: {len(df.columns)}')
