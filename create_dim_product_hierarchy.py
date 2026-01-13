"""
Create Dimension Table for Product Hierarchy (PH Level 3)

Star Schema Design:
- Dimension: dim_product_hierarchy
- Fact: fact_production_performance_v2
- Join Key: material_code (cleaned, no leading zeros)

Purpose: Enable loss categorization by Brand/Grade (PH Level 3)
Reference: ADR Production V3.5
"""
from sqlalchemy import text
from src.db.connection import SessionLocal

def create_dim_product_hierarchy():
    db = SessionLocal()
    try:
        print("Creating dimension table: dim_product_hierarchy")
        
        # Create dimension table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_product_hierarchy (
                material_code VARCHAR(50) PRIMARY KEY,
                material_description TEXT,
                ph_level_1 VARCHAR(100),
                ph_level_2 VARCHAR(100),
                ph_level_3 VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("  ✓ Table created")
        
        # Create index on PH Level 3 for fast filtering
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_dim_ph3 
            ON dim_product_hierarchy(ph_level_3)
        """))
        print("  ✓ Index on ph_level_3 created")
        
        # Create index on PH Level 2 for additional filtering
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_dim_ph2 
            ON dim_product_hierarchy(ph_level_2)
        """))
        print("  ✓ Index on ph_level_2 created")
        
        db.commit()
        print("\n🎉 Dimension table ready for master data!")
        
        # Check existing data
        result = db.execute(text("SELECT COUNT(*) FROM dim_product_hierarchy")).fetchone()
        print(f"Current records: {result[0]}")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_dim_product_hierarchy()
