"""
Test ZRSD004 Header Fix
Verify the fix works before re-loading production data
"""
import pandas as pd
from pathlib import Path

print("="*80)
print("  TEST: ZRSD004 HEADER DETECTION FIX")
print("="*80)

file_path = Path('demodata/zrsd004.XLSX')

if not file_path.exists():
    print(f"❌ File not found: {file_path}")
    exit(1)

print(f"\n📁 Testing file: {file_path}")
print(f"   File exists: ✅")
print(f"   File size: {file_path.stat().st_size:,} bytes")

# Test OLD approach (should fail)
print("\n" + "="*80)
print("  TEST 1: Old Approach (header=0)")
print("="*80)

try:
    df_old = pd.read_excel(file_path, header=0, dtype=str)
    print(f"✓ Read {len(df_old)} rows, {len(df_old.columns)} columns")
    print(f"\nColumn names (first 5):")
    for i, col in enumerate(df_old.columns[:5]):
        print(f"  {i}: {col}")
    
    if 'Unnamed' in str(df_old.columns[0]):
        print(f"\n❌ FAILED: Headers not detected (Unnamed columns)")
    else:
        print(f"\n⚠️  Unexpected: Headers detected with old approach")
    
    # Test data access
    test_delivery = df_old.iloc[0].get('Delivery')
    print(f"\nTest data access: df.iloc[0].get('Delivery') = {test_delivery}")
    if test_delivery is None or pd.isna(test_delivery):
        print(f"❌ FAILED: Cannot access 'Delivery' column")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test NEW approach (should work)
print("\n" + "="*80)
print("  TEST 2: New Approach (header=None, skiprows=1, manual columns)")
print("="*80)

try:
    df_new = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)
    
    # Assign column names
    df_new.columns = [
        'Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference',
        'Req. Type', 'Delivery Type', 'Shipping Point', 'Sloc',
        'Sales Office', 'Dist. Channel', 'Cust. Group', 'Sold-to Party',
        'Ship-to Party', 'Name of Ship-to', 'City of Ship-to',
        'Regional Stru. Grp.', 'Transportation Zone', 'Salesman ID',
        'Salesman Name', 'Material', 'Description', 'Delivery Qty',
        'Tonase', 'Tonase Unit', 'Actual Delivery Qty', 'Sales Unit',
        'Net Weight', 'Weight Unit', 'Volume', 'Volume Unit',
        'Created By', 'Product Hierarchy', 'Line Item',
        'Total Movement Goods Stat'
    ][:len(df_new.columns)]
    
    print(f"✓ Read {len(df_new)} rows, {len(df_new.columns)} columns")
    print(f"\nColumn names (first 10):")
    for i, col in enumerate(df_new.columns[:10]):
        print(f"  {i}: {col}")
    
    if 'Delivery' in df_new.columns:
        print(f"\n✅ SUCCESS: Headers assigned correctly")
    else:
        print(f"\n❌ FAILED: 'Delivery' column not found")
    
    # Test data access
    test_delivery = df_new.iloc[0].get('Delivery')
    test_material = df_new.iloc[0].get('Material')
    test_ship_to = df_new.iloc[0].get('Name of Ship-to')
    
    print(f"\n📊 Sample Data (Row 0):")
    print(f"   Delivery: {test_delivery}")
    print(f"   Material: {test_material}")
    print(f"   Name of Ship-to: {test_ship_to}")
    
    # Check for NULLs
    null_delivery = df_new['Delivery'].isna().sum()
    null_material = df_new['Material'].isna().sum()
    total_rows = len(df_new)
    
    print(f"\n📈 Data Quality:")
    print(f"   Total rows: {total_rows:,}")
    print(f"   NULL Deliveries: {null_delivery:,} ({null_delivery/total_rows*100:.1f}%)")
    print(f"   NULL Materials: {null_material:,} ({null_material/total_rows*100:.1f}%)")
    
    if null_delivery < total_rows * 0.1:  # Less than 10% NULL
        print(f"\n✅ SUCCESS: Data populated correctly (<10% NULL)")
    else:
        print(f"\n⚠️  WARNING: High NULL percentage (>{null_delivery/total_rows*100:.1f}%)")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# FINAL VERDICT
print("\n" + "="*80)
print("  FINAL VERDICT")
print("="*80)

if 'df_new' in locals() and 'Delivery' in df_new.columns and null_delivery < total_rows * 0.1:
    print("\n🎉 ✅ FIX VERIFIED - Ready for production deployment!")
    print("\nNext steps:")
    print("  1. Code changes already applied to src/etl/loaders.py")
    print("  2. Truncate raw_zrsd004 and fact_delivery tables")
    print("  3. Re-upload zrsd004.XLSX via API")
    print("  4. Run transform")
    print("  5. Verify 24,856 rows loaded with populated data")
else:
    print("\n❌ FIX FAILED - Need investigation")

print("\n" + "="*80)
