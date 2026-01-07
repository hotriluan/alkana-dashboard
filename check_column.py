from src.db.connection import SessionLocal, engine
from src.db.models import Base, FactLeadTime
from sqlalchemy import inspect

db = SessionLocal()

try:
    # Check if channel_code column exists
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('fact_lead_time')]
    
    print("=== FACT_LEAD_TIME COLUMNS ===")
    for col in columns:
        print(f"  - {col}")
        
    if 'channel_code' in columns:
        print("\n[OK] channel_code column EXISTS")
    else:
        print("\n[ERROR] channel_code column MISSING")
        print("\nNeed to add column manually or recreate table")
        
finally:
    db.close()
