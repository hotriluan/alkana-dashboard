"""
Truncate all yield data to allow fresh re-upload

This script clears:
- fact_production_performance_v2 (analytical table)
- raw_zrpp062 (staging table)
"""
from src.db.connection import SessionLocal
from sqlalchemy import text

def truncate_yield_data():
    db = SessionLocal()
    try:
        print("Truncating yield data tables...")
        
        # Truncate fact table
        db.execute(text("TRUNCATE TABLE fact_production_performance_v2 CASCADE"))
        print("  ✓ Truncated fact_production_performance_v2")
        
        # Truncate raw staging table
        db.execute(text("TRUNCATE TABLE raw_zrpp062 CASCADE"))
        print("  ✓ Truncated raw_zrpp062")
        
        db.commit()
        print("\n🎉 All yield data cleared successfully!")
        print("You can now re-upload all months with the fixed loader.")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    truncate_yield_data()
