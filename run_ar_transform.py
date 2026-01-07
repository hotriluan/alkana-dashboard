"""Transform AR data from raw to fact"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from db.database import get_db
from etl.transform import DataTransformer

print("Running AR transform...")
db = next(get_db())
transformer = DataTransformer(db)
transformer.transform_ar_aging()
db.close()

print("\n✅ Transform complete!")

# Verify
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://postgres:password123@localhost:5432/alkana_dashboard")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            snapshot_date,
            COUNT(*) as rows,
            SUM(total_target) as target,
            SUM(total_realization) as realization
        FROM fact_ar_aging
        GROUP BY snapshot_date
    """)).fetchall()
    
    print("\nFact AR Aging:")
    for row in result:
        print(f"  {row[0]}: {row[1]} rows, Target: {row[2]:,.0f}, Realization: {row[3]:,.0f}")
