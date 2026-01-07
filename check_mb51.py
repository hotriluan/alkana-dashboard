import pandas as pd
import openpyxl

# Check mb51.XLSX structure
wb = openpyxl.load_workbook('demodata/mb51.XLSX')
ws = wb.active

print('First 3 rows from openpyxl:')
for i, row in enumerate(ws.iter_rows(min_row=1, max_row=3, values_only=True)):
    print(f'Row {i+1}:', row[:10], '...')

print('\n' + '='*60)
print('Pandas read (default):')
df = pd.read_excel('demodata/mb51.XLSX', nrows=2)
print('Columns:', list(df.columns))
print(df)
