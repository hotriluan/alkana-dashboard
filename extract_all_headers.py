import openpyxl
from pathlib import Path

# All demo files
files = {
    '11.XLSX': 'ZRSD006',
    '12.XLSX': 'ZRSD006', 
    '13.XLSX': 'ZRSD006',
    '15.XLSX': 'ZRSD006',
    'cooispi.XLSX': 'COOISPI',
    'mb51.XLSX': 'MB51',
    'target.xlsx': 'TARGET',
    'ZRFI005.XLSX': 'ZRFI005',
    'zrmm024.XLSX': 'ZRMM024',
    'zrpp062.XLSX': 'ZRPP062',
    'zrsd002.xlsx': 'ZRSD002',
    'zrsd004.XLSX': 'ZRSD004',
}

demodata = Path('demodata')

print("="*80)
print("COMPREHENSIVE HEADER EXTRACTION - ALL DEMO FILES")
print("="*80)

for filename, expected_type in files.items():
    fpath = demodata / filename
    if not fpath.exists():
        print(f"\n❌ {filename} - FILE NOT FOUND")
        continue
    
    try:
        wb = openpyxl.load_workbook(fpath)
        ws = wb.active
        row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        headers = [str(h) for h in row if h and h != 'None']
        wb.close()
        
        print(f"\n{'='*80}")
        print(f"📄 {filename} (Expected: {expected_type})")
        print(f"{'='*80}")
        print(f"Total columns: {len(headers)}")
        print(f"First 15 columns:")
        for i, h in enumerate(headers[:15], 1):
            print(f"  {i:2d}. {h}")
        
    except Exception as e:
        print(f"\n❌ {filename} - ERROR: {e}")
