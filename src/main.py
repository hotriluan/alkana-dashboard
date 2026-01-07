"""
Main entry point for Alkana Dashboard ELT Pipeline

Usage:
    python -m src.main init      # Initialize database
    python -m src.main load      # Load raw data
    python -m src.main transform # Transform to warehouse
    python -m src.main run       # Full pipeline
    python -m src.main test      # Test connection
"""
import sys
import argparse
from datetime import datetime

from src.db.connection import test_connection, init_db, engine, SessionLocal
from src.db.models import Base
from src.etl.loaders import load_all_raw_data
from src.etl.transform import Transformer


def cmd_init():
    """Initialize database - create all tables"""
    print("\n" + "=" * 60)
    print("INITIALIZING DATABASE")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created")


def cmd_load():
    """Load all raw data from Excel files"""
    print("\n" + "=" * 60)
    print("LOADING RAW DATA")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        results = load_all_raw_data(db)
        
        print("\nLoad Summary:")
        for name, stats in results.items():
            print(f"  {name}: {stats.get('loaded', 0)} rows")
    finally:
        db.close()


def cmd_truncate():
    """Truncate warehouse tables (facts and dimensions)"""
    print("\n" + "=" * 60)
    print("TRUNCATING WAREHOUSE TABLES")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        transformer = Transformer(db)
        transformer.truncate_warehouse()
    finally:
        db.close()


def cmd_transform():
    """Transform raw data to warehouse"""
    print("\n" + "=" * 60)
    print("TRANSFORMING DATA")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        transformer = Transformer(db)
        transformer.transform_all()
    finally:
        db.close()


def cmd_run():
    """Run full ELT pipeline"""
    start_time = datetime.now()
    
    print("\n" + "=" * 60)
    print("ALKANA DASHBOARD - ELT PIPELINE")
    print(f"Started: {start_time}")
    print("=" * 60)
    
    # Step 1: Test connection
    if not test_connection():
        print("✗ Database connection failed. Aborting.")
        sys.exit(1)
    
    # Step 2: Initialize database
    cmd_init()
    
    # Step 3: Load raw data
    cmd_load()
    
    # Step 4: Truncate warehouse (prevent duplication)
    cmd_truncate()
    
    # Step 5: Transform
    cmd_transform()
    
    # Done
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print(f"Duration: {duration:.2f} seconds")
    print("=" * 60)


def cmd_test():
    """Test database connection"""
    print("\nTesting database connection...")
    if test_connection():
        print("✓ Connection successful!")
    else:
        print("✗ Connection failed!")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Alkana Dashboard ELT Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  init      Initialize database (create tables)
  load      Load raw data from Excel files
  transform Transform raw data to warehouse
  truncate  Truncate warehouse tables (prevent duplication)
  run       Run full ELT pipeline
  test      Test database connection
        """
    )
    
    parser.add_argument(
        'command',
        choices=['init', 'load', 'transform', 'truncate', 'run', 'test'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    commands = {
        'init': cmd_init,
        'load': cmd_load,
        'transform': cmd_transform,
        'truncate': cmd_truncate,
        'run': cmd_run,
        'test': cmd_test,
    }
    
    commands[args.command]()


if __name__ == '__main__':
    main()
