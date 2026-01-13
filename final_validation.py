#!/usr/bin/env python3
"""
Final Comprehensive Validation - All 12 Demo Files
Tests that all detection signatures work correctly
"""
import openpyxl
from pathlib import Path
from typing import Dict, List, Tuple

# EXACT signatures from fileDetection.ts (synchronized)
DETECTION_RULES = {
    'ZRPP062': ['MRP controller', 'Product Group 1', 'Product Group 2', 'Process Order', 'Batch'],
    'ZRSD006': ['Material Code', 'PH 1', 'PH 2', 'PH 3'],
    'COOISPI': ['Plant', 'Sales Order', 'Order', 'Material Number'],
    'MB51': ['Posting Date', 'Movement Type', 'Material Document', 'Qty in Un. of Entry', 'Storage Location'],
    'ZRMM024': ['Purch. Order', 'Item', 'Purch. Date', 'Suppl. Plant', 'Dest. Plant'],
    'ZRSD002': ['Billing Document', 'Net Value', 'Billing Date', 'Material'],
    'ZRSD004': ['Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference'],
    'ZRFI005': ['Company Code', 'Profit Center', 'Customer Code', 'Target 1-30 Days'],
    'TARGET': ['Salesman Name', 'Semester', 'Year', 'Target'],
}

# Expected file type mapping
EXPECTED_TYPES = {
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

def detect_file_type(headers: List[str]) -> Tuple[str, int, int]:
    """Detect file type using same logic as fileDetection.ts"""
    for file_type, signature in DETECTION_RULES.items():
        matches = [sig for sig in signature if sig in headers]
        threshold = len(signature) * 0.6
        
        if len(matches) >= threshold:
            return (file_type, len(matches), len(signature))
    
    return ('UNKNOWN', 0, 0)

def main():
    print("\n" + "="*80)
    print("FINAL COMPREHENSIVE VALIDATION - V4 SMART INGESTION")
    print("="*80)
    print(f"Testing {len(EXPECTED_TYPES)} demo files\n")
    
    results = []
    passed = 0
    failed = 0
    
    for filename, expected_type in sorted(EXPECTED_TYPES.items()):
        file_path = Path('demodata') / filename
        
        # Read headers
        try:
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            headers = [str(cell.value) for cell in ws[1] if cell.value]
            wb.close()
        except Exception as e:
            print(f"❌ {filename}: ERROR reading file - {e}")
            results.append((filename, 'ERROR', expected_type, 0, 0))
            failed += 1
            continue
        
        # Detect type
        detected_type, matches, total = detect_file_type(headers)
        match_rate = (matches / total * 100) if total > 0 else 0
        
        # Validate
        if detected_type == expected_type:
            status = '✅ PASS'
            passed += 1
            print(f"{status} {filename:<20} → {detected_type:<10} ({matches}/{total} = {match_rate:.0f}%)")
        else:
            status = '❌ FAIL'
            failed += 1
            print(f"{status} {filename:<20} → Expected: {expected_type}, Got: {detected_type}")
        
        results.append((filename, detected_type, expected_type, matches, total))
    
    # Summary
    print("\n" + "="*80)
    print(f"RESULTS: {passed}/{len(EXPECTED_TYPES)} files passed ({passed/len(EXPECTED_TYPES)*100:.0f}%)")
    print("="*80)
    
    if failed > 0:
        print("\n❌ FAILURES:")
        for filename, detected, expected, matches, total in results:
            if detected != expected:
                print(f"   {filename}: Expected {expected}, got {detected}")
    else:
        print("\n✅ ALL FILES DETECTED CORRECTLY!")
        print("\nDetection Rate by File Type:")
        type_counts = {}
        for filename, detected, expected, matches, total in results:
            if expected not in type_counts:
                type_counts[expected] = []
            type_counts[expected].append((filename, matches, total))
        
        for file_type in sorted(type_counts.keys()):
            files = type_counts[file_type]
            print(f"\n  {file_type}:")
            for filename, matches, total in files:
                match_rate = matches / total * 100
                print(f"    - {filename}: {matches}/{total} signatures ({match_rate:.0f}%)")
    
    return passed == len(EXPECTED_TYPES)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
