from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # Check if view exists
    result = db.execute(text("""
        SELECT COUNT(*) 
        FROM information_schema.views 
        WHERE table_name = 'view_yield_dashboard'
    """)).fetchone()
    
    print(f"=== VIEW_YIELD_DASHBOARD ===")
    print(f"Exists: {result[0] > 0}")
    
    if result[0] > 0:
        # Get view definition
        view_def = db.execute(text("""
            SELECT view_definition 
            FROM information_schema.views 
            WHERE table_name = 'view_yield_dashboard'
        """)).fetchone()
        
        print(f"\nView Definition:")
        print(view_def[0])
        
        # Get sample data
        sample = db.execute(text("""
            SELECT * FROM view_yield_dashboard LIMIT 5
        """)).fetchall()
        
        print(f"\n=== SAMPLE DATA ===")
        print(f"Records: {len(sample)}")
        
        if sample:
            # Get column names
            cols = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'view_yield_dashboard'
                ORDER BY ordinal_position
            """)).fetchall()
            
            print(f"\nColumns: {[c[0] for c in cols]}")
            print(f"\nFirst record:")
            for i, col in enumerate(cols):
                print(f"  {col[0]}: {sample[0][i]}")
    
finally:
    db.close()
