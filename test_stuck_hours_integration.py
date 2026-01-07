"""
Integration test for stuck hours fix using real demo data

Skills: testing, backend-development, databases
CLAUDE.md: Integration test with real data to verify end-to-end fix
"""
import pandas as pd
from datetime import datetime

from src.db.connection import SessionLocal
from src.db.models import FactAlert, RawMb51
from src.core.alerts import AlertDetector
from src.core.uom_converter import UomConverter


def test_batch_25L2492010_stuck_hours():
    """
    Integration test: Verify batch 25L2492010 shows correct stuck hours
    
    Expected:
    - MVT 101 at Plant 1401: 2025-12-18
    - MVT 601 at Plant 1401: 2025-12-22
    - Stuck hours: 96.0 (4 days × 24 hours)
    - NOT 207.3 hours
    """
    print("=" * 80)
    print("INTEGRATION TEST: Batch 25L2492010 Stuck Hours")
    print("=" * 80)
    
    # Load MB51 data from demo files
    print("\n1. Loading demo data...")
    mb51_df = pd.read_excel('demodata/mb51.XLSX')
    
    # Rename columns to match expected format
    mb51_df.columns = [
        'col_0_posting_date', 'col_1_mvt_type', 'col_2_plant', 'col_3_sloc',
        'col_4_material', 'col_5_material_desc', 'col_6_batch', 'col_7_qty',
        'col_8_uom', 'col_9_cost_center', 'col_10_gl_account', 'col_11_material_doc',
        'col_12_reference', 'col_13_outbound_delivery', 'col_14', 'col_15_purchase_order'
    ]
    
    # Convert posting date to datetime
    mb51_df['col_0_posting_date'] = pd.to_datetime(mb51_df['col_0_posting_date'])
    
    print(f"   Loaded {len(mb51_df)} MB51 records")
    
    # Verify batch 25L2492010 data
    print("\n2. Verifying batch 25L2492010 movements...")
    batch_data = mb51_df[mb51_df['col_6_batch'] == '25L2492010'].copy()
    batch_data = batch_data.sort_values('col_0_posting_date')
    
    print(f"   Found {len(batch_data)} movements for batch 25L2492010:")
    for _, row in batch_data.iterrows():
        mvt = int(row['col_1_mvt_type']) if pd.notna(row['col_1_mvt_type']) else 0
        print(f"     {row['col_0_posting_date']} | MVT {mvt:3d} | Plant {row['col_2_plant']} | SLoc {row['col_3_sloc']}")
    
    # Find MVT 101 and MVT 601 at Plant 1401
    mvt_101_1401 = batch_data[(batch_data['col_1_mvt_type'] == 101) & (batch_data['col_2_plant'] == 1401)]
    mvt_601_1401 = batch_data[(batch_data['col_1_mvt_type'] == 601) & (batch_data['col_2_plant'] == 1401)]
    
    if not mvt_101_1401.empty and not mvt_601_1401.empty:
        receipt_date = mvt_101_1401['col_0_posting_date'].values[0]
        issue_date = mvt_601_1401['col_0_posting_date'].values[0]
        
        receipt_dt = pd.to_datetime(receipt_date)
        issue_dt = pd.to_datetime(issue_date)
        
        expected_hours = (issue_dt - receipt_dt).total_seconds() / 3600
        
        print(f"\n   Receipt (MVT 101): {receipt_dt}")
        print(f"   Issue (MVT 601): {issue_dt}")
        print(f"   Expected stuck hours: {expected_hours:.1f}")
    
    # Run alert detection
    print("\n3. Running alert detection...")
    uom_converter = UomConverter()
    detector = AlertDetector(
        mb51_df=mb51_df,
        uom_converter=uom_converter,
        stuck_threshold_hours=48
    )
    
    # Detect alerts at Plant 1401
    alerts = detector.detect_stuck_in_transit(plant=1401)
    
    print(f"   Detected {len(alerts)} alerts at Plant 1401")
    
    # Find alert for batch 25L2492010
    batch_alerts = [a for a in alerts if a.batch == '25L2492010']
    
    print(f"\n4. Verifying batch 25L2492010 alert...")
    if len(batch_alerts) == 0:
        print("   ✗ FAILED: No alert found for batch 25L2492010")
        print("   This might be expected if the batch is not P01 or doesn't meet criteria")
        return False
    
    alert = batch_alerts[0]
    print(f"   Alert type: {alert.alert_type}")
    print(f"   Stuck hours: {alert.metric_value}")
    print(f"   Severity: {alert.severity}")
    print(f"   Message: {alert.message}")
    
    # Verify stuck hours
    print("\n5. Verification Results:")
    if alert.metric_value == 96.0:
        print(f"   ✓ PASSED: Stuck hours = {alert.metric_value} (correct!)")
        print(f"   ✓ NOT 207.3 hours (bug fixed!)")
        return True
    else:
        print(f"   ✗ FAILED: Expected 96.0 hours, got {alert.metric_value}")
        return False


def test_no_stuck_in_transit_alerts():
    """
    Verify that no STUCK_IN_TRANSIT alerts are created
    (only DELAYED_TRANSIT alerts should exist)
    """
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: No STUCK_IN_TRANSIT Alerts")
    print("=" * 80)
    
    # Load MB51 data
    mb51_df = pd.read_excel('demodata/mb51.XLSX')
    mb51_df.columns = [
        'col_0_posting_date', 'col_1_mvt_type', 'col_2_plant', 'col_3_sloc',
        'col_4_material', 'col_5_material_desc', 'col_6_batch', 'col_7_qty',
        'col_8_uom', 'col_9_cost_center', 'col_10_gl_account', 'col_11_material_doc',
        'col_12_reference', 'col_13_outbound_delivery', 'col_14', 'col_15_purchase_order'
    ]
    mb51_df['col_0_posting_date'] = pd.to_datetime(mb51_df['col_0_posting_date'])
    
    # Run alert detection
    uom_converter = UomConverter()
    detector = AlertDetector(
        mb51_df=mb51_df,
        uom_converter=uom_converter
    )
    
    alerts = detector.detect_stuck_in_transit(plant=1401)
    
    # Check alert types
    stuck_in_transit = [a for a in alerts if a.alert_type == 'STUCK_IN_TRANSIT']
    delayed_transit = [a for a in alerts if a.alert_type == 'DELAYED_TRANSIT']
    
    print(f"\n   Total alerts: {len(alerts)}")
    print(f"   STUCK_IN_TRANSIT: {len(stuck_in_transit)}")
    print(f"   DELAYED_TRANSIT: {len(delayed_transit)}")
    
    if len(stuck_in_transit) == 0:
        print(f"\n   ✓ PASSED: No STUCK_IN_TRANSIT alerts (correct!)")
        print(f"   ✓ Only DELAYED_TRANSIT alerts created")
        return True
    else:
        print(f"\n   ✗ FAILED: Found {len(stuck_in_transit)} STUCK_IN_TRANSIT alerts")
        print(f"   These should have been removed!")
        return False


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("RUNNING INTEGRATION TESTS FOR STUCK HOURS FIX")
    print("=" * 80)
    
    # Run tests
    test1_passed = test_batch_25L2492010_stuck_hours()
    test2_passed = test_no_stuck_in_transit_alerts()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Batch 25L2492010): {'PASSED ✓' if test1_passed else 'FAILED ✗'}")
    print(f"Test 2 (No STUCK_IN_TRANSIT): {'PASSED ✓' if test2_passed else 'FAILED ✗'}")
    print("=" * 80)
    
    if test1_passed and test2_passed:
        print("\n✓ ALL TESTS PASSED!")
        exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        exit(1)
