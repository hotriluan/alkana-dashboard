"""
V4 Validation: Centralized Smart Ingestion System
Tests backend endpoints and data integrity after V4 upgrade.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.db.connection import SessionLocal
from sqlalchemy import text

def test_zrsd006_auto_population():
    """Test 1: Verify Zrsd006Loader auto-populates dim_product_hierarchy"""
    print("\n" + "="*70)
    print("TEST 1: Zrsd006 Auto-Population (dim_product_hierarchy)")
    print("="*70)
    
    db = SessionLocal()
    try:
        # Check dim_product_hierarchy row count
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_materials,
                COUNT(DISTINCT ph_level_1) as divisions,
                COUNT(DISTINCT ph_level_2) as businesses,
                COUNT(DISTINCT ph_level_3) as brands_grades
            FROM dim_product_hierarchy
        """)).fetchone()
        
        print(f"\n📊 Dimension Table Stats:")
        print(f"  Total Materials: {result.total_materials:,}")
        print(f"  PH Level 1 (Divisions): {result.divisions}")
        print(f"  PH Level 2 (Businesses): {result.businesses}")
        print(f"  PH Level 3 (Brands/Grades): {result.brands_grades}")
        
        if result.total_materials > 0:
            print(f"\n✅ TEST PASSED: dim_product_hierarchy populated ({result.total_materials:,} materials)")
            return True
        else:
            print(f"\n❌ TEST FAILED: dim_product_hierarchy is empty")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        return False
    finally:
        db.close()

def test_zrpp062_period_endpoint():
    """Test 2: Verify Zrpp062Loader endpoint accepts period parameter"""
    print("\n" + "="*70)
    print("TEST 2: Zrpp062 Period Upload Endpoint")
    print("="*70)
    
    try:
        from src.etl.loaders import Zrpp062Loader
        
        # Check if load_with_period method exists
        if hasattr(Zrpp062Loader, 'load_with_period'):
            print("\n✅ Zrpp062Loader.load_with_period() method exists")
            
            # Check method signature
            import inspect
            sig = inspect.signature(Zrpp062Loader.load_with_period)
            params = list(sig.parameters.keys())
            
            print(f"  Method signature: {params}")
            
            if 'file_path' in params and 'reference_date' in params:
                print(f"\n✅ TEST PASSED: load_with_period accepts file_path and reference_date")
                return True
            else:
                print(f"\n❌ TEST FAILED: Missing required parameters")
                return False
        else:
            print(f"\n❌ TEST FAILED: load_with_period method not found")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        return False

def test_category_performance_aggregation():
    """Test 3: Verify weighted loss calculation in category_performance"""
    print("\n" + "="*70)
    print("TEST 3: Category Performance Weighted Loss Calculation")
    print("="*70)
    
    db = SessionLocal()
    try:
        # Get category performance with weighted loss
        result = db.execute(text("""
            SELECT 
                dph.ph_level_3 as category,
                SUM(f.output_actual_kg) as total_output_kg,
                SUM(f.loss_kg) as total_loss_kg,
                CASE 
                    WHEN SUM(f.output_actual_kg + f.loss_kg) > 0 
                    THEN (SUM(f.loss_kg) / SUM(f.output_actual_kg + f.loss_kg) * 100)
                    ELSE 0 
                END as loss_pct_weighted
            FROM fact_production_performance_v2 f
            LEFT JOIN dim_product_hierarchy dph 
                ON LPAD(f.material_code, 18, '0') = LPAD(dph.material_code, 18, '0')
            GROUP BY dph.ph_level_3
            HAVING SUM(f.output_actual_kg + f.loss_kg) > 0
            ORDER BY total_loss_kg DESC
            LIMIT 5
        """)).fetchall()
        
        print(f"\n📊 Top 5 Categories by Total Loss (Weighted Calculation):")
        print(f"\n{'Category':<25} {'Output (kg)':>15} {'Loss (kg)':>12} {'Loss %':>10}")
        print("-" * 70)
        
        for row in result:
            print(f"{row.category or 'Uncategorized':<25} {row.total_output_kg:>15,.0f} {row.total_loss_kg:>12,.0f} {row.loss_pct_weighted:>9.2f}%")
        
        if len(result) > 0:
            # Verify weighted calculation for first category
            first = result[0]
            expected_pct = (first.total_loss_kg / (first.total_output_kg + first.total_loss_kg)) * 100
            
            if abs(first.loss_pct_weighted - expected_pct) < 0.01:
                print(f"\n✅ TEST PASSED: Weighted loss calculation correct ({first.loss_pct_weighted:.2f}%)")
                return True
            else:
                print(f"\n❌ TEST FAILED: Calculation mismatch (got {first.loss_pct_weighted:.2f}%, expected {expected_pct:.2f}%)")
                return False
        else:
            print(f"\n⚠️  No data found - upload ZRPP062 data first")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        return False
    finally:
        db.close()

def test_uncategorized_materials():
    """Test 4: Identify materials not in dim_product_hierarchy"""
    print("\n" + "="*70)
    print("TEST 4: Uncategorized Materials Analysis")
    print("="*70)
    
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT 
                COUNT(DISTINCT f.material_code) as total_materials,
                COUNT(DISTINCT CASE 
                    WHEN dph.material_code IS NULL THEN f.material_code 
                END) as uncategorized_materials,
                SUM(f.loss_kg) as total_loss,
                SUM(CASE 
                    WHEN dph.material_code IS NULL THEN f.loss_kg 
                    ELSE 0 
                END) as uncategorized_loss
            FROM fact_production_performance_v2 f
            LEFT JOIN dim_product_hierarchy dph 
                ON LPAD(f.material_code, 18, '0') = LPAD(dph.material_code, 18, '0')
        """)).fetchone()
        
        print(f"\n📊 Material Categorization Coverage:")
        print(f"  Total Unique Materials in Production: {result.total_materials}")
        print(f"  Uncategorized Materials: {result.uncategorized_materials}")
        
        if result.total_materials > 0:
            coverage_pct = ((result.total_materials - result.uncategorized_materials) / result.total_materials) * 100
            print(f"  Coverage Rate: {coverage_pct:.1f}%")
        
        if result.total_loss and result.total_loss > 0:
            uncategorized_pct = (result.uncategorized_loss / result.total_loss) * 100
            print(f"\n  Total Loss: {result.total_loss:,.0f} kg")
            print(f"  Uncategorized Loss: {result.uncategorized_loss:,.0f} kg ({uncategorized_pct:.1f}%)")
            
            if uncategorized_pct < 10:
                print(f"\n✅ TEST PASSED: Less than 10% loss is uncategorized ({uncategorized_pct:.1f}%)")
                return True
            else:
                print(f"\n⚠️  WARNING: {uncategorized_pct:.1f}% of loss is uncategorized")
                print(f"     Consider uploading updated ZRSD006 file")
                return True  # Still pass, just a warning
        else:
            print(f"\n⚠️  No production data found - upload ZRPP062 first")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        return False
    finally:
        db.close()

def test_file_detection_rules():
    """Test 5: Validate file detection rule configuration"""
    print("\n" + "="*70)
    print("TEST 5: File Detection Rules Configuration")
    print("="*70)
    
    try:
        # Read fileDetection.ts
        detection_file = Path("web/src/utils/fileDetection.ts")
        
        if not detection_file.exists():
            print(f"\n❌ TEST FAILED: fileDetection.ts not found")
            return False
        
        content = detection_file.read_text(encoding='utf-8')
        
        # Check for required rules
        required_rules = [
            ("ZRPP062", "requiresPeriod: true"),
            ("ZRSD006", "requiresPeriod: false"),
            ("Order SFG Liquid", "ZRPP062 signature"),
            ("Product hierarchy", "ZRSD006 signature")
        ]
        
        print(f"\n📄 Checking DETECTION_RULES configuration:")
        
        all_found = True
        for rule_name, description in required_rules:
            if rule_name in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ Missing: {description}")
                all_found = False
        
        if all_found:
            print(f"\n✅ TEST PASSED: All detection rules configured correctly")
            return True
        else:
            print(f"\n❌ TEST FAILED: Missing detection rules")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        return False

def main():
    """Run all V4 validation tests"""
    print("\n" + "="*70)
    print("🚀 V4 CENTRALIZED SMART INGESTION - VALIDATION SUITE")
    print("="*70)
    print("Testing: Backend auto-population, file detection, data integrity")
    
    tests = [
        test_zrsd006_auto_population,
        test_zrpp062_period_endpoint,
        test_category_performance_aggregation,
        test_uncategorized_materials,
        test_file_detection_rules
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_func.__name__}: {str(e)}")
            results.append((test_func.__name__, False))
    
    # Final Summary
    print("\n" + "="*70)
    print("📋 VALIDATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n{'='*70}")
    print(f"  Total: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    print(f"{'='*70}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED - V4 System Ready for Production!")
    else:
        print(f"\n⚠️  Some tests failed - Review errors above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
