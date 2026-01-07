"""
Final analysis for batch 25L2492010 stuck hours calculation
"""

import pandas as pd
from datetime import datetime

print("=" * 100)
print("PHAN TICH STUCK HOURS CHO BATCH 25L2492010")
print("=" * 100)

# Load data
mb51 = pd.read_excel('demodata/mb51.XLSX')
cooispi = pd.read_excel('demodata/cooispi.XLSX')

batch = '25L2492010'

# Get COOISPI data
cooispi_data = cooispi[cooispi['Batch'] == batch]
if not cooispi_data.empty:
    actual_finish = pd.to_datetime(cooispi_data['Actual finish date'].values[0])
    print(f"\nCOOISPI - Actual finish date: {actual_finish}")
    print("(Ngay san xuat hoan thanh tai nha may)")

# Get MB51 data
batch_movements = mb51[mb51['Batch'] == batch].copy()
batch_movements['Posting Date'] = pd.to_datetime(batch_movements['Posting Date'])
batch_movements = batch_movements.sort_values('Posting Date')

print(f"\nMB51 - Cac giao dich vat tu:")
print("-" * 100)
for _, row in batch_movements.iterrows():
    mvt = int(row['Movement Type']) if pd.notna(row['Movement Type']) else 0
    print(f"  {row['Posting Date']} | MVT {mvt:3d} | Plant {row['Plant']} | SLoc {row['Storage Location']}")

# Get MVT 101 at Plant 1401
mvt_101_1401 = batch_movements[(batch_movements['Movement Type'] == 101) & (batch_movements['Plant'] == 1401)]
mvt_601_1401 = batch_movements[(batch_movements['Movement Type'] == 601) & (batch_movements['Plant'] == 1401)]

print("\n" + "=" * 100)
print("LOGIC TINH STUCK HOURS CUA HE THONG:")
print("=" * 100)

if not mvt_101_1401.empty:
    receipt_date = pd.to_datetime(mvt_101_1401['Posting Date'].values[0])
    print(f"\n1. Thoi diem BAT DAU tinh: MVT 101 tai Plant 1401 (DC)")
    print(f"   Ngay: {receipt_date}")
    print(f"   Y nghia: Hang da NHAN tai kho thanh pham DC")
    
    if not mvt_601_1401.empty:
        issue_date = pd.to_datetime(mvt_601_1401['Posting Date'].values[0])
        print(f"\n2. Thoi diem KET THUC tinh: MVT 601 tai Plant 1401 (DC)")
        print(f"   Ngay: {issue_date}")
        print(f"   Y nghia: Hang da XUAT tu kho thanh pham DC")
        
        stuck_hours = (issue_date - receipt_date).total_seconds() / 3600
        print(f"\n3. STUCK HOURS = {stuck_hours:.1f} hours")
        print(f"   Tinh tu: {receipt_date}")
        print(f"   Den: {issue_date}")
        print(f"   Loai: DELAYED_TRANSIT (da xuat nhung cham)")
    else:
        current_time = datetime.now()
        stuck_hours = (current_time - receipt_date).total_seconds() / 3600
        print(f"\n2. Thoi diem KET THUC tinh: HIEN TAI (chua co MVT 601)")
        print(f"   Ngay: {current_time}")
        print(f"   Y nghia: Hang CHUA DUOC XUAT tu kho thanh pham DC")
        
        print(f"\n3. STUCK HOURS = {stuck_hours:.1f} hours")
        print(f"   Tinh tu: {receipt_date}")
        print(f"   Den: {current_time}")
        print(f"   Loai: STUCK_IN_TRANSIT (dang stuck)")

print("\n" + "=" * 100)
print("TOM TAT:")
print("=" * 100)
print("\nHe thong KHONG su dung 'Actual finish date' tu COOISPI de tinh stuck hours!")
print("\nStuck hours duoc tinh nhu sau:")
print("  - BAT DAU: Khi hang NHAN tai DC (MVT 101 at Plant 1401)")
print("  - KET THUC: Khi hang XUAT tu DC (MVT 601 at Plant 1401) HOAC thoi gian hien tai")
print("\nVoi batch 25L2492010:")
print(f"  - Actual finish date (COOISPI): {actual_finish} <- KHONG dung cho stuck hours")
print(f"  - MVT 101 at Plant 1401: {receipt_date} <- BAT DAU tinh stuck")
if not mvt_601_1401.empty:
    print(f"  - MVT 601 at Plant 1401: {issue_date} <- KET THUC tinh stuck")
    print(f"  - Stuck hours: {stuck_hours:.1f} hours (DELAYED_TRANSIT)")
else:
    print(f"  - MVT 601 at Plant 1401: CHUA CO <- Van dang stuck")
    print(f"  - Current time: {current_time}")
    print(f"  - Stuck hours: {stuck_hours:.1f} hours (STUCK_IN_TRANSIT)")

print("\n" + "=" * 100)
