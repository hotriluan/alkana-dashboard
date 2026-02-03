#!/usr/bin/env python3
"""
Production Inventory Data Diagnostic Script

Checks if production database has proper inventory movement data
and identifies why Top 10 High Velocity/Dead Stock might be empty.

Usage:
    python diagnose_production_inventory.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.connection import SessionLocal
from sqlalchemy import text
from datetime import datetime, timedelta
import json


def diagnose_inventory():
    """Diagnose inventory data issues"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("PRODUCTION INVENTORY DATA DIAGNOSTIC")
        print("=" * 70)
        
        # Check 1: Database connection
        print("\n[1/6] Testing database connection...")
        result = db.execute(text("SELECT current_database(), version()"))
        db_name, version = result.fetchone()
        print(f"✓ Connected to: {db_name}")
        print(f"✓ PostgreSQL: {version[:50]}...")
        
        # Check 2: fact_inventory table exists
        print("\n[2/6] Checking fact_inventory table...")
        result = db.execute(text("""
            SELECT COUNT(*) FROM fact_inventory
        """))
        total_records = result.fetchone()[0]
        print(f"✓ Total records in fact_inventory: {total_records:,}")
        
        if total_records == 0:
            print("⚠️  WARNING: No data in fact_inventory table!")
            print("   → Production database needs data load")
            return
        
        # Check 3: Movement types distribution
        print("\n[3/6] Analyzing movement types...")
        result = db.execute(text("""
            SELECT mvt_type, COUNT(*) as count
            FROM fact_inventory
            GROUP BY mvt_type
            ORDER BY count DESC
            LIMIT 10
        """))
        mvt_types = result.fetchall()
        print(f"✓ Found {len(mvt_types)} movement types")
        for mvt_type, count in mvt_types[:5]:
            print(f"  • mvt_type {mvt_type}: {count:,} records")
        
        # Check if outbound types exist
        outbound_types = [999, 601, 261]
        result = db.execute(text("""
            SELECT mvt_type, COUNT(*) as count
            FROM fact_inventory
            WHERE mvt_type IN :types
            GROUP BY mvt_type
        """), {"types": tuple(outbound_types)})
        found_outbound = result.fetchall()
        
        if not found_outbound:
            print(f"\n⚠️  WARNING: No outbound movement types found!")
            print(f"   Expected: {outbound_types}")
            print(f"   → All items will show velocity=0")
        else:
            print(f"\n✓ Found outbound types:")
            for mvt_type, count in found_outbound:
                print(f"  • mvt_type {mvt_type}: {count:,} records")
        
        # Check 4: Date range analysis
        print("\n[4/6] Analyzing date ranges...")
        result = db.execute(text("""
            SELECT 
                MIN(posting_date) as min_date,
                MAX(posting_date) as max_date,
                COUNT(DISTINCT posting_date) as distinct_days
            FROM fact_inventory
        """))
        min_date, max_date, distinct_days = result.fetchone()
        print(f"✓ Date range: {min_date} to {max_date}")
        print(f"✓ Distinct days: {distinct_days}")
        
        # Check data in last 90 days
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=90)
        
        result = db.execute(text("""
            SELECT COUNT(*)
            FROM fact_inventory
            WHERE posting_date >= :start_date
              AND posting_date <= :end_date
        """), {"start_date": start_date, "end_date": end_date})
        recent_count = result.fetchone()[0]
        print(f"✓ Records in last 90 days: {recent_count:,}")
        
        # Check 5: Material codes analysis
        print("\n[5/6] Analyzing material codes...")
        result = db.execute(text("""
            SELECT 
                COUNT(DISTINCT material_code) as total_materials,
                COUNT(DISTINCT CASE WHEN material_code LIKE '10%' THEN material_code END) as fg_count,
                COUNT(DISTINCT CASE WHEN material_code LIKE '12%' THEN material_code END) as sfg_count,
                COUNT(DISTINCT CASE WHEN material_code LIKE '15%' THEN material_code END) as rm_count
            FROM fact_inventory
        """))
        total_mat, fg, sfg, rm = result.fetchone()
        print(f"✓ Total materials: {total_mat:,}")
        print(f"  • Finish Goods (10xx): {fg:,}")
        print(f"  • Semi-Finish (12xx): {sfg:,}")
        print(f"  • Raw Materials (15xx): {rm:,}")
        
        # Check 6: Simulate velocity query
        print("\n[6/6] Simulating Top Movers query (last 90 days)...")
        result = db.execute(text("""
            SELECT 
                material_code,
                material_description,
                COUNT(*) as velocity
            FROM fact_inventory
            WHERE posting_date >= :start_date
              AND posting_date <= :end_date
              AND mvt_type IN :outbound_types
              AND (material_code LIKE '10%' OR material_code LIKE '12%' OR material_code LIKE '15%')
            GROUP BY material_code, material_description
            HAVING COUNT(*) > 0
            ORDER BY velocity DESC
            LIMIT 10
        """), {
            "start_date": start_date,
            "end_date": end_date,
            "outbound_types": tuple(outbound_types)
        })
        top_movers = result.fetchall()
        
        if top_movers:
            print(f"✓ Found {len(top_movers)} high velocity items:")
            for material, desc, velocity in top_movers[:5]:
                print(f"  • {material[:25]:25s}: {velocity:3d} movements")
        else:
            print("⚠️  No high velocity items found!")
            print("   Possible causes:")
            print("   1. No outbound movements (601/261/999) in last 90 days")
            print("   2. Date range has no data")
            print("   3. Material codes don't match filter (10%/12%/15%)")
        
        # Summary
        print("\n" + "=" * 70)
        print("DIAGNOSIS SUMMARY")
        print("=" * 70)
        
        issues = []
        if total_records == 0:
            issues.append("❌ No data in fact_inventory table")
        if not found_outbound:
            issues.append("❌ No outbound movement types (999/601/261)")
        if recent_count == 0:
            issues.append("❌ No data in last 90 days")
        if not top_movers:
            issues.append("❌ No high velocity items found")
        
        if issues:
            print("\n⚠️  ISSUES DETECTED:")
            for issue in issues:
                print(f"  {issue}")
            print("\n💡 RECOMMENDED ACTIONS:")
            if total_records == 0:
                print("  1. Load data using: python -m src.main load")
            elif not found_outbound:
                print("  1. Check movement type mappings in source data")
                print("  2. Update OUTBOUND_MVT_TYPES in inventory_analytics.py")
            elif recent_count == 0:
                print("  1. Upload recent data (last 90 days)")
            else:
                print("  1. Check date filter logic in API endpoint")
                print("  2. Verify material code prefixes match data")
        else:
            print("\n✅ All checks passed!")
            print("   If dashboard still shows no data:")
            print("   1. Check API endpoint: /api/v1/dashboards/inventory/top-movers-and-dead-stock")
            print("   2. Check browser console for errors")
            print("   3. Verify frontend API_BASE_URL points to correct backend")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    diagnose_inventory()
