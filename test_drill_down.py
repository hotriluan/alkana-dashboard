"""
Test drill-down endpoint with sample categories
"""
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import text
from db.connection import SessionLocal

def main():
    db = SessionLocal()
    
    # Check available categories
    print("📊 Available PH Level 3 Categories (Sample):")
    result = db.execute(text("""
        SELECT DISTINCT d.ph_level_3, COUNT(*) as material_count
        FROM dim_product_hierarchy d
        WHERE d.ph_level_3 IS NOT NULL
        GROUP BY d.ph_level_3
        ORDER BY material_count DESC
        LIMIT 10
    """)).fetchall()
    
    for row in result:
        print(f"  • {row[0]}: {row[1]} materials")
    
    # Test drill-down query with a category
    if result:
        test_category = result[0][0]
        print(f"\n🔍 Testing Drill-Down for Category: '{test_category}'")
        
        drill_result = db.execute(text("""
            SELECT 
                f.material_code,
                MAX(f.material_description) as material_description,
                COUNT(*) as order_count
            FROM fact_production_performance_v2 f
            LEFT JOIN dim_product_hierarchy d ON f.material_code = d.material_code
            WHERE d.ph_level_3 = :category
            GROUP BY f.material_code
            ORDER BY order_count DESC
            LIMIT 5
        """), {'category': test_category}).fetchall()
        
        if drill_result:
            print(f"  Found {len(drill_result)} materials:")
            for row in drill_result:
                print(f"    - {row[0]}: {row[1]} ({row[2]} orders)")
        else:
            print(f"  ⚠️  No production data found for category '{test_category}'")
    
    db.close()

if __name__ == "__main__":
    main()
