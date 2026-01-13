"""
V4 File Detection Validation
Tests all demo files against detection rules
Compliance: Claude Kit - sequential-thinking + debugging skills
"""
import sys
import io
from pathlib import Path
import openpyxl

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

# File detection signature mapping (from fileDetection.ts)
# Updated: 2025-01-XX - All signatures verified against actual demo file headers
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

def get_excel_headers(file_path: Path) -> list:
    """Extract column headers from Excel file"""
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True)
        ws = wb.active
        headers = [cell for cell in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
        wb.close()
        return [str(h) for h in headers if h and h != 'None']
    except Exception as e:
        print(f"  ❌ Error reading: {e}")
        return []

def detect_file_type(headers: list) -> tuple:
    """Match headers against detection rules"""
    for file_type, signature in DETECTION_RULES.items():
        match_count = sum(1 for sig in signature if any(sig in h for h in headers))
        threshold = len(signature) * 0.6
        
        if match_count >= threshold:
            return (file_type, match_count, len(signature))
    
    return (None, 0, 0)

def test_all_files():
    """Test detection for all demo files"""
    demodata = Path(__file__).parent / 'demodata'
    files = sorted(demodata.glob('*.xlsx'))
    
    print("\n" + "="*80)
    print("FILE DETECTION VALIDATION - V4 SMART INGESTION")
    print("="*80)
    print(f"Testing {len(files)} files from demodata/\n")
    
    results = []
    
    for file_path in files:
        if 'uploads' in str(file_path):
            continue
            
        print(f"📄 {file_path.name}")
        
        # Get headers
        headers = get_excel_headers(file_path)
        if not headers:
            results.append((file_path.name, 'ERROR', 'Cannot read file', []))
            continue
        
        print(f"  Headers ({len(headers)}): {', '.join(headers[:10])}...")
        
        # Detect type
        detected_type, matches, total = detect_file_type(headers)
        
        if detected_type:
            confidence = (matches / total) * 100
            print(f"  ✅ Detected: {detected_type} ({matches}/{total} signatures = {confidence:.0f}%)")
            results.append((file_path.name, detected_type, 'PASS', headers))
        else:
            print(f"  ❌ Not detected (no signature match)")
            results.append((file_path.name, 'UNKNOWN', 'FAIL', headers))
        
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r[2] == 'PASS')
    failed = sum(1 for r in results if r[2] == 'FAIL')
    errors = sum(1 for r in results if r[2] == 'ERROR')
    
    print(f"\n{'File':<20} {'Detected Type':<15} {'Status':<10}")
    print("-"*50)
    for name, detected, status, _ in results:
        status_icon = '✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'
        print(f"{name:<20} {detected:<15} {status_icon} {status}")
    
    print(f"\n{'='*80}")
    print(f"PASSED: {passed}/{len(results)} ({(passed/len(results)*100):.0f}%)")
    print(f"FAILED: {failed}/{len(results)}")
    print(f"ERRORS: {errors}/{len(results)}")
    print(f"{'='*80}\n")
    
    # Detailed failures
    if failed > 0:
        print("\n🔍 FAILURE ANALYSIS:\n")
        for name, detected, status, headers in results:
            if status == 'FAIL':
                print(f"❌ {name}")
                print(f"   Headers: {headers[:15]}")
                print(f"   Needs: Manual signature rule creation\n")
    
    return passed == len(results)

if __name__ == "__main__":
    success = test_all_files()
    sys.exit(0 if success else 1)
