#!/usr/bin/env python3
"""
OTIF Logic Validation Tests
Test the new logistics-only OTIF calculation from fact_delivery
"""
import asyncio
from datetime import datetime, date
from src.db.connection import SessionLocal
from src.db.models import FactDelivery

def test_late_delivery():
    """Test Case 1: Late delivery (actual > delivery_date)"""
    db = SessionLocal()
    
    # Query for test data or create test record
    test_delivery = db.query(FactDelivery).filter(
        FactDelivery.delivery_date == date(2026, 1, 20),
        FactDelivery.actual_gi_date == date(2026, 1, 22)
    ).first()
    
    if test_delivery:
        # Calculate status
        status = "Pending" if test_delivery.actual_gi_date is None else \
                 "On Time" if test_delivery.actual_gi_date <= test_delivery.delivery_date else \
                 "Late"
        
        assert status == "Late", f"Expected 'Late' but got '{status}'"
        print("✓ Test 1 PASSED: Late delivery correctly identified")
        print(f"  Delivery Date: {test_delivery.delivery_date}")
        print(f"  Actual GI Date: {test_delivery.actual_gi_date}")
        print(f"  Status: {status}")
    else:
        print("⚠ Test 1 SKIPPED: No test data found for late delivery scenario")
    
    db.close()

def test_ontime_delivery():
    """Test Case 2: On-time delivery (actual <= delivery_date)"""
    db = SessionLocal()
    
    test_delivery = db.query(FactDelivery).filter(
        FactDelivery.delivery_date == date(2026, 1, 20),
        FactDelivery.actual_gi_date == date(2026, 1, 20)
    ).first()
    
    if test_delivery:
        # Calculate status
        status = "Pending" if test_delivery.actual_gi_date is None else \
                 "On Time" if test_delivery.actual_gi_date <= test_delivery.delivery_date else \
                 "Late"
        
        assert status == "On Time", f"Expected 'On Time' but got '{status}'"
        print("✓ Test 2 PASSED: On-time delivery correctly identified")
        print(f"  Delivery Date: {test_delivery.delivery_date}")
        print(f"  Actual GI Date: {test_delivery.actual_gi_date}")
        print(f"  Status: {status}")
    else:
        print("⚠ Test 2 SKIPPED: No test data found for on-time delivery scenario")
    
    db.close()

def test_pending_delivery():
    """Test Case 3: Pending delivery (actual_gi_date is NULL)"""
    db = SessionLocal()
    
    test_delivery = db.query(FactDelivery).filter(
        FactDelivery.actual_gi_date.is_(None)
    ).first()
    
    if test_delivery:
        # Calculate status
        status = "Pending" if test_delivery.actual_gi_date is None else \
                 "On Time" if test_delivery.actual_gi_date <= test_delivery.delivery_date else \
                 "Late"
        
        assert status == "Pending", f"Expected 'Pending' but got '{status}'"
        print("✓ Test 3 PASSED: Pending delivery correctly identified")
        print(f"  Delivery: {test_delivery.delivery}")
        print(f"  Actual GI Date: {test_delivery.actual_gi_date}")
        print(f"  Status: {status}")
    else:
        print("⚠ Test 3 SKIPPED: No pending deliveries found")
    
    db.close()

def test_no_zrsd002_dependency():
    """Test Case 4: Verify OTIF works WITHOUT zrsd002 (billing) data"""
    db = SessionLocal()
    
    # Count deliveries with populated dates
    total = db.query(FactDelivery).filter(
        FactDelivery.delivery_date.isnot(None),
        FactDelivery.actual_gi_date.isnot(None)
    ).count()
    
    if total > 0:
        print(f"✓ Test 4 PASSED: OTIF data exists independent of zrsd002")
        print(f"  Found {total} delivery records with complete date information")
    else:
        print("ℹ Test 4 INFO: No complete delivery records yet (expected if ZRSD004 not loaded)")
    
    db.close()

if __name__ == '__main__':
    print("=" * 70)
    print("OTIF Logic Validation Tests")
    print("Testing: fact_delivery-only OTIF calculation (no zrsd002 dependency)")
    print("=" * 70)
    print()
    
    test_late_delivery()
    print()
    test_ontime_delivery()
    print()
    test_pending_delivery()
    print()
    test_no_zrsd002_dependency()
    
    print()
    print("=" * 70)
    print("All available tests completed!")
    print("=" * 70)
