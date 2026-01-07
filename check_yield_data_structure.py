from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("=== CHECKING FACT_P02_P01_YIELD DATA ===\n")
    
    # Check total records
    total = db.execute(text("SELECT COUNT(*) FROM fact_p02_p01_yield")).fetchone()[0]
    print(f"Total P02→P01 pairs: {total}")
    
    # Check unique materials
    unique_p01 = db.execute(text("""
        SELECT COUNT(DISTINCT p01_material_code) 
        FROM fact_p02_p01_yield
    """)).fetchone()[0]
    
    unique_p02 = db.execute(text("""
        SELECT COUNT(DISTINCT p02_material_code) 
        FROM fact_p02_p01_yield
    """)).fetchone()[0]
    
    print(f"Unique P01 materials: {unique_p01}")
    print(f"Unique P02 materials: {unique_p02}")
    
    # Sample data
    print(f"\n=== SAMPLE RECORDS ===")
    samples = db.execute(text("""
        SELECT 
            p02_batch,
            p01_batch,
            p02_material_code,
            p02_material_desc,
            p01_material_code,
            p01_material_desc,
            p02_consumed_kg,
            p01_produced_kg,
            yield_pct
        FROM fact_p02_p01_yield
        ORDER BY yield_pct ASC
        LIMIT 5
    """)).fetchall()
    
    for i, row in enumerate(samples, 1):
        print(f"\n{i}. Batch: {row[0]} → {row[1]}")
        print(f"   P02: {row[3]} ({row[2]})")
        print(f"   P01: {row[5]} ({row[4]})")
        print(f"   Input: {row[6]} KG → Output: {row[7]} KG")
        print(f"   Yield: {row[8]}%")
    
    # Check if data aggregates correctly by material
    print(f"\n=== MATERIAL AGGREGATION TEST ===")
    
    # Group by P01 material
    material_agg = db.execute(text("""
        SELECT 
            p01_material_code,
            p01_material_desc,
            COUNT(*) as batch_count,
            SUM(p02_consumed_kg) as total_input,
            SUM(p01_produced_kg) as total_output,
            AVG(yield_pct) as avg_yield
        FROM fact_p02_p01_yield
        GROUP BY p01_material_code, p01_material_desc
        ORDER BY avg_yield ASC
        LIMIT 5
    """)).fetchall()
    
    print("\nLowest yield materials (aggregated):")
    for row in material_agg:
        print(f"\n{row[1]} ({row[0]})")
        print(f"  Batches: {row[2]}")
        print(f"  Total Input: {row[3]:.2f} KG")
        print(f"  Total Output: {row[4]:.2f} KG")
        print(f"  Avg Yield: {row[5]:.2f}%")
    
finally:
    db.close()
