import openpyxl

wb = openpyxl.load_workbook('demodata/zrsd004.XLSX')
ws = wb.active
headers = [cell.value for cell in ws[1]]

print('Full header list from zrsd004.XLSX:')
print('=' * 80)
for i, h in enumerate(headers):
    if h is not None:
        print(f'{i:2d}: {h}')
    else:
        break

print(f'\nTotal columns with headers: {len([h for h in headers if h is not None])}')
