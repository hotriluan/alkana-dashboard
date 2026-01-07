"""
Deploy ZRSD004 Fix via API Upload

This script uses the upload API endpoint to reload ZRSD004 data
with the fixed Zrsd004Loader that properly handles Excel headers.

Skills: backend-development, testing
"""
import requests
from pathlib import Path
import time
from sqlalchemy import text
from src.db.connection import SessionLocal

def main():
    # Configuration
    API_BASE = "http://localhost:8000/api/v1"
    ZRSD004_FILE = Path("demodata/zrsd004.XLSX")
    
    if not ZRSD004_FILE.exists():
        print(f"❌ File not found: {ZRSD004_FILE}")
        return
    
    print("=" * 80)
    print("PHASE 4: ZRSD004 Header Fix Deployment via API")
    print("=" * 80)
    
    # STEP 1: Check current state
    print("\n[STEP 1] Before Fix - Database State")
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT COUNT(*) FROM raw_zrsd004")).scalar()
        print(f"  raw_zrsd004: {result:,} rows")
        
        null_deliveries = db.execute(text(
            "SELECT COUNT(*) FROM raw_zrsd004 WHERE delivery IS NULL"
        )).scalar()
        null_pct = (null_deliveries / result * 100) if result > 0 else 0
        print(f"  NULL Deliveries: {null_deliveries:,} ({null_pct:.1f}%)")
        
        fact_count = db.execute(text("SELECT COUNT(*) FROM fact_delivery")).scalar()
        print(f"  fact_delivery: {fact_count:,} rows")
        
        if null_pct > 90:
            print("  ❌ Data is corrupted (>90% NULL) - fix needed!")
        else:
            print("  ✅ Data looks healthy")
    finally:
        db.close()
    
    # STEP 2: Truncate tables (to ensure clean reload)
    print("\n[STEP 2] Truncating Tables for Clean Reload")
    db = SessionLocal()
    try:
        db.execute(text("TRUNCATE TABLE raw_zrsd004 CASCADE"))
        db.execute(text("TRUNCATE TABLE fact_delivery CASCADE"))
        db.commit()
        print("  ✓ Tables truncated")
    except Exception as e:
        db.rollback()
        print(f"  ❌ Truncate failed: {e}")
        return
    finally:
        db.close()
    
    # STEP 3: Upload file via API
    print("\n[STEP 3] Uploading ZRSD004 via API (with fixed loader)")
    try:
        with open(ZRSD004_FILE, 'rb') as f:
            files = {'file': (ZRSD004_FILE.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(f"{API_BASE}/upload/", files=files, timeout=300)
        
        if response.status_code == 200:
            data = response.json()
            upload_id = data.get('upload_id')
            print(f"  ✓ Upload started: ID={upload_id}")
            print(f"  Status: {data.get('status')}")
            print(f"  Message: {data.get('message')}")
            
            # STEP 4: Wait for processing to complete
            print("\n[STEP 4] Waiting for Processing to Complete")
            for i in range(60):  # Wait up to 60 seconds
                time.sleep(1)
                status_response = requests.get(f"{API_BASE}/upload/{upload_id}/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    current_status = status_data.get('status')
                    print(f"  [{i+1}s] Status: {current_status}", end='\r')
                    
                    if current_status == 'completed':
                        print(f"\n  ✅ Processing completed!")
                        print(f"     Rows loaded: {status_data.get('rows_loaded', 0):,}")
                        print(f"     Rows updated: {status_data.get('rows_updated', 0):,}")
                        print(f"     Rows failed: {status_data.get('rows_failed', 0):,}")
                        break
                    elif current_status == 'failed':
                        print(f"\n  ❌ Processing failed!")
                        print(f"     Error: {status_data.get('error_message')}")
                        return
            else:
                print("\n  ⚠️ Timeout waiting for processing")
                
        else:
            print(f"  ❌ Upload failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return
            
    except requests.exceptions.ConnectionError:
        print("  ❌ Cannot connect to API - is the backend running?")
        print("  Run: uvicorn src.main:app --reload")
        return
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return
    
    # STEP 5: Verify the fix
    print("\n[STEP 5] Verifying Fix")
    db = SessionLocal()
    try:
        # Check raw_zrsd004
        total_rows = db.execute(text("SELECT COUNT(*) FROM raw_zrsd004")).scalar()
        null_deliveries = db.execute(text(
            "SELECT COUNT(*) FROM raw_zrsd004 WHERE delivery IS NULL"
        )).scalar()
        null_materials = db.execute(text(
            "SELECT COUNT(*) FROM raw_zrsd004 WHERE material_code IS NULL"
        )).scalar()
        
        null_pct = (null_deliveries / total_rows * 100) if total_rows > 0 else 0
        
        print(f"  raw_zrsd004:")
        print(f"    Total rows: {total_rows:,}")
        print(f"    NULL Deliveries: {null_deliveries:,} ({null_pct:.1f}%)")
        print(f"    NULL Materials: {null_materials:,}")
        
        # Check fact_delivery
        fact_count = db.execute(text("SELECT COUNT(*) FROM fact_delivery")).scalar()
        print(f"  fact_delivery: {fact_count:,} rows")
        
        # Sample data
        sample = db.execute(text(
            "SELECT delivery, material_code, ship_to_name, city FROM raw_zrsd004 LIMIT 3"
        )).fetchall()
        
        print(f"\n  Sample Data:")
        for row in sample:
            print(f"    Delivery: {row[0]}, Material: {row[1]}, Ship-to: {row[2]}, City: {row[3]}")
        
        # Final verdict
        print("\n" + "=" * 80)
        if null_pct < 5 and total_rows > 20000:
            print("🎉 ✅ DEPLOYMENT SUCCESSFUL!")
            print(f"   - {total_rows:,} rows loaded with {null_pct:.1f}% NULL rate")
            print(f"   - fact_delivery populated with {fact_count:,} rows")
            print("   - Phase 4 (ZRSD004 Headers) COMPLETE")
        elif null_pct < 50:
            print("⚠️ PARTIAL SUCCESS")
            print(f"   - Data loaded but {null_pct:.1f}% NULL rate is higher than expected (<5%)")
        else:
            print("❌ DEPLOYMENT FAILED")
            print(f"   - {null_pct:.1f}% NULL rate indicates headers still broken")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
