"""
Add snapshot_date column to fact_ar_aging table
Enables time-series analysis of AR aging data
"""
from sqlalchemy import text, create_engine
from pathlib import Path

# Database connection
DATABASE_URL = "postgresql://postgres:password123@localhost:5432/alkana_dashboard"
engine = create_engine(DATABASE_URL)

def add_snapshot_date_column():
    """Add snapshot_date column to fact_ar_aging"""
    
    with engine.begin() as conn:
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fact_ar_aging' 
            AND column_name = 'snapshot_date'
        """)
        result = conn.execute(check_query).fetchone()
        
        if result:
            print("✅ Column snapshot_date already exists")
            return
        
        # Add snapshot_date column
        print("Adding snapshot_date column to fact_ar_aging...")
        conn.execute(text("""
            ALTER TABLE fact_ar_aging 
            ADD COLUMN snapshot_date DATE
        """))
        
        # Populate snapshot_date from report_date for existing records
        print("Populating snapshot_date from report_date...")
        result = conn.execute(text("""
            UPDATE fact_ar_aging 
            SET snapshot_date = report_date 
            WHERE snapshot_date IS NULL AND report_date IS NOT NULL
        """))
        print(f"  Updated {result.rowcount} rows")
        
        # Add index for better query performance
        print("Creating index on snapshot_date...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fact_ar_aging_snapshot_date 
            ON fact_ar_aging(snapshot_date)
        """))
        
        print("\n✅ Migration complete!")
        
        # Show sample data
        print("\nSample data with snapshot_date:")
        sample = conn.execute(text("""
            SELECT snapshot_date, report_date, COUNT(*) as row_count
            FROM fact_ar_aging
            GROUP BY snapshot_date, report_date
            ORDER BY snapshot_date DESC
            LIMIT 5
        """)).fetchall()
        
        for row in sample:
            print(f"  Snapshot: {row[0]}, Report: {row[1]}, Rows: {row[2]}")

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Add snapshot_date to fact_ar_aging")
    print("=" * 60)
    add_snapshot_date_column()
