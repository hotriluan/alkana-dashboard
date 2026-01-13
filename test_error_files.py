#!/usr/bin/env python3
"""Test the 6 ERROR files directly"""
import openpyxl
from pathlib import Path

# File detection rules
DETECTION_RULES = {
    'ZRSD006': ['Material Code', 'PH 1', 'PH 2', 'PH 3'],
    'COOISPI': ['Plant', 'Sales Order', 'Order', 'Material Number'],
    'ZRMM024': ['Purch. Order', 'Item', 'Purch. Date', 'Suppl. Plant', 'Dest. Plant'],
}

error_files = ['11.XLSX', '12.XLSX', '13.XLSX', '15.XLSX', 'cooispi.XLSX', 'zrmm024.XLSX']

for filename in error_files:
    file_path = Path('demodata') / filename
    print(f"\n{'='*60}")
    print(f"📄 {filename}")
    print('='*60)
    
    try:
        # Read with openpyxl
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        headers = [str(cell.value) for cell in ws[1] if cell.value]
        print(f"Headers ({len(headers)}): {headers[:10]}")
        
        # Check against rules
        expected_type = 'ZRSD006' if filename in ['11.XLSX', '12.XLSX', '13.XLSX', '15.XLSX'] else \
                       'COOISPI' if filename == 'cooispi.XLSX' else 'ZRMM024'
        
        signature = DETECTION_RULES[expected_type]
        matches = [sig for sig in signature if sig in headers]
        match_rate = len(matches) / len(signature) * 100
        
        print(f"\nExpected type: {expected_type}")
        print(f"Signature: {signature}")
        print(f"Matches: {matches}")
        print(f"Match rate: {match_rate:.0f}% (threshold: 60%)")
        
        if match_rate >= 60:
            print(f"✅ Should detect as {expected_type}")
        else:
            print(f"❌ Would NOT detect (insufficient matches)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
