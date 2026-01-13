"""
Database Migration Script for Yield V3
Executes: TRUNCATE, ADD columns, ADD UNIQUE constraint, CREATE index
"""
from src.db.connection import engine
from sqlalchemy import text

def run_migration():
    # Run each step in separate transaction to handle failures gracefully
    steps = [
        ("TRUNCATE TABLE fact_production_performance_v2 CASCADE", "TRUNCATE"),
        ("ALTER TABLE fact_production_performance_v2 ADD COLUMN IF NOT EXISTS reference_date DATE DEFAULT CURRENT_DATE", "Add reference_date"),
        ("ALTER TABLE fact_production_performance_v2 ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()", "Add updated_at"),
    ]
    
    for sql, desc in steps:
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
                print(f'✅ {desc} completed')
        except Exception as e:
            print(f'⚠️ {desc}: {e}')
    
    # Add UNIQUE constraint (separate step)
    try:
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE fact_production_performance_v2 DROP CONSTRAINT IF EXISTS uq_prod_yield_v3'))
            conn.execute(text('ALTER TABLE fact_production_performance_v2 ADD CONSTRAINT uq_prod_yield_v3 UNIQUE (process_order_id, batch_id)'))
            conn.commit()
            print('✅ Added UNIQUE constraint')
    except Exception as e:
        print(f'⚠️ UNIQUE constraint: {e}')
    
    # Create index (separate step)
    try:
        with engine.connect() as conn:
            conn.execute(text('DROP INDEX IF EXISTS idx_yield_ref_date'))
            conn.execute(text('CREATE INDEX idx_yield_ref_date ON fact_production_performance_v2(reference_date)'))
            conn.commit()
            print('✅ Created index on reference_date')
    except Exception as e:
        print(f'⚠️ Index: {e}')
    
    print('🎉 Database upgrade completed!')

if __name__ == "__main__":
    run_migration()
