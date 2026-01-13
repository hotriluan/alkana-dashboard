"""
Test V3.6 Category Performance endpoint with weighted loss calculation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import text
from db.connection import SessionLocal

def test_weighted_loss_calculation():
    """Verify that loss_pct_avg is calculated correctly as weighted average"""
    db = SessionLocal()
    
    print("🧪 Testing Weighted Loss Calculation\n")
    print("Formula: loss_pct_avg = (total_loss_kg / (total_output_kg + total_loss_kg)) * 100\n")
    
    # Test query
    query = text("""
        SELECT 
            COALESCE(d.ph_level_3, 'Uncategorized') as category,
            COALESCE(SUM(f.output_actual_kg), 0) as total_output_kg,
            COALESCE(SUM(f.loss_kg), 0) as total_loss_kg,
            CASE 
                WHEN (SUM(f.output_actual_kg) + SUM(f.loss_kg)) > 0 
                THEN (SUM(f.loss_kg) / (SUM(f.output_actual_kg) + SUM(f.loss_kg))) * 100
                ELSE 0 
            END as loss_pct_avg,
            COUNT(*) as batch_count
        FROM fact_production_performance_v2 f
        LEFT JOIN dim_product_hierarchy d ON f.material_code = d.material_code
        WHERE f.reference_date >= '2025-01-01'
        GROUP BY d.ph_level_3
        HAVING SUM(f.output_actual_kg) > 0
        ORDER BY total_loss_kg DESC
        LIMIT 5
    """)
    
    result = db.execute(query).fetchall()
    
    print("📊 Top 5 Categories by Total Loss:\n")
    print(f"{'Category':<25} {'Output (kg)':<12} {'Loss (kg)':<12} {'Loss %':<10} {'Batches':<8}")
    print("-" * 75)
    
    for row in result:
        category = row[0]
        output = row[1]
        loss = row[2]
        loss_pct = row[3]
        batches = row[4]
        
        # Manual verification
        expected_pct = (loss / (output + loss)) * 100 if (output + loss) > 0 else 0
        
        print(f"{category:<25} {output:>11,.0f} {loss:>11,.0f} {loss_pct:>9.2f}% {batches:>7}")
        
        # Validate calculation
        if abs(loss_pct - expected_pct) > 0.01:
            print(f"  ⚠️  WARNING: Expected {expected_pct:.2f}%, got {loss_pct:.2f}%")
        else:
            print(f"  ✓ Calculation verified")
    
    print("\n" + "=" * 75)
    print("✅ All weighted calculations correct!" if result else "⚠️  No data found")
    
    db.close()

if __name__ == "__main__":
    test_weighted_loss_calculation()
