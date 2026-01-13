import openpyxl
from pathlib import Path

files = ['11.XLSX', 'cooispi.XLSX', 'zrmm024.XLSX']
demodata = Path('demodata')

for f in files:
    try:
        fpath = demodata / f
        wb = openpyxl.load_workbook(fpath)
        ws = wb.active
        row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        headers = [str(h) for h in row if h and h != 'None']
        print(f'{f}: {headers[:8]}')
        wb.close()
    except Exception as e:
        print(f'{f}: ERROR - {e}')
