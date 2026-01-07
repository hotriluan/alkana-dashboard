"""
Database Migration Script - Add Lead-time Columns

Adds 7 lead-time tracking columns to fact_production table.
Reference: NEXT_STEPS.md Phase 6.1.1

Run: python scripts/migrate_leadtime_columns.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.db.connection import engine

def migrate_leadtime_columns():
    """Add lead-time columns to fact_production table"""
    
    print("="*60)
    print("DATABASE MIGRATION: Add Lead-time Columns")
    print("="*60)
    
    migrations = [
        {
            "name": "prep_time_days",
            "sql": "ALTER TABLE fact_production ADD COLUMN IF NOT EXISTS prep_time_days INTEGER",
            "description": "MTO only: PO Date → Release"
        },
        {
            "name": "production_time_days",
            "sql": "ALTER TABLE fact_production ADD COLUMN IF NOT EXISTS production_time_days INTEGER",
            "description": "Release → Finish"
        },
        {
            "name": "transit_time_days",
            "sql": "ALTER TABLE fact_production ADD COLUMN IF NOT EXISTS transit_time_days INTEGER",
            "description": "Finish → Receipt (MVT 101)"
        },
        {
            "name": "storage_time_days",
            "sql": "ALTER TABLE fact_production ADD COLUMN IF NOT EXISTS storage_time_days INTEGER",
            "description": "Receipt → Issue (MVT 601 netted)"
        },
        {
            "name": "delivery_time_days",
            "sql": "ALTER TABLE fact_production ADD COLUMN IF NOT EXISTS delivery_time_days INTEGER",
            "description": "MTO only: Issue → Actual GI"
        },
        {
            "name": "total_leadtime_days",
            "sql": "ALTER TABLE fact_production ADD COLUMN IF NOT EXISTS total_leadtime_days INTEGER",
            "description": "Sum of all components"
        },
        {
            "name": "leadtime_status",
            "sql": "ALTER TABLE fact_production ADD COLUMN IF NOT EXISTS leadtime_status VARCHAR(20)",
            "description": "ON_TIME, DELAYED, CRITICAL, UNKNOWN"
        }
    ]
    
    with engine.begin() as conn:
        for migration in migrations:
            try:
                print(f"\n✓ Adding column: {migration['name']}")
                print(f"  Description: {migration['description']}")
                conn.execute(text(migration['sql']))
                print(f"  Status: SUCCESS")
            except Exception as e:
                print(f"  Status: FAILED - {str(e)}")
        
        # Create indexes for performance
        print("\n✓ Creating indexes...")
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_leadtime_status ON fact_production(leadtime_status)"))
            print("  - idx_leadtime_status: SUCCESS")
        except Exception as e:
            print(f"  - idx_leadtime_status: FAILED - {str(e)}")
        
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_total_leadtime ON fact_production(total_leadtime_days)"))
            print("  - idx_total_leadtime: SUCCESS")
        except Exception as e:
            print(f"  - idx_total_leadtime: FAILED - {str(e)}")
    
    print("\n" + "="*60)
    print("MIGRATION COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Run ETL transform to populate lead-time data")
    print("2. Verify data: SELECT * FROM fact_production WHERE total_leadtime_days IS NOT NULL LIMIT 5;")
    print("3. Test API: GET /api/v1/leadtime/summary")


if __name__ == "__main__":
    migrate_leadtime_columns()
