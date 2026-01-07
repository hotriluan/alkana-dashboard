"""
Add fact_p02_p01_yield table for P02→P01 yield tracking

Run: python add_p02_p01_yield_table.py
"""
from src.db.connection import SessionLocal, engine
from sqlalchemy import text

db = SessionLocal()

try:
    print("Creating fact_p02_p01_yield table...")
    
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS fact_p02_p01_yield (
            id SERIAL PRIMARY KEY,
            p02_batch VARCHAR(50) NOT NULL,
            p01_batch VARCHAR(50) NOT NULL,
            p02_material_code VARCHAR(50),
            p02_material_desc TEXT,
            p01_material_code VARCHAR(50),
            p01_material_desc TEXT,
            p02_consumed_kg NUMERIC(15,3),
            p01_produced_kg NUMERIC(15,3),
            yield_pct NUMERIC(5,2),
            loss_kg NUMERIC(15,3),
            production_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    print("Creating indexes...")
    
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_p02_p01_yield_batches 
        ON fact_p02_p01_yield(p02_batch, p01_batch)
    """))
    
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_p02_p01_yield_pct 
        ON fact_p02_p01_yield(yield_pct)
    """))
    
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_p02_p01_yield_date 
        ON fact_p02_p01_yield(production_date)
    """))
    
    db.commit()
    
    print("✓ Table and indexes created successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
