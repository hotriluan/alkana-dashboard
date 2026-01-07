"""
Emergency restore - reload all data from Excel files
All raw tables were accidentally wiped
"""

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import sys

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

async def main():
    print("="*80)
    print("EMERGENCY RESTORE - RELOADING ALL DATA FROM EXCEL")
    print("="*80)
    
    # Add src to path
    sys.path.insert(0, 'src')
    
    # Import and run the ETL pipeline
    from src.etl.loaders import load_all_raw_data
    from src.etl.transform import Transformer
    
    print("\n📥 Step 1: Loading from Excel files...")
    session = Session()
    load_all_raw_data(session)
    
    print("\n📊 Step 2: Transforming to fact tables...")
    transformer = Transformer(session)
    transformer.transform_all()
    session.close()
    
    # Validate counts
    session = Session()
    from sqlalchemy import text
    
    print("\n="*80)
    print("VALIDATION - RAW TABLES")
    print("="*80)
    
    raw_tables = ['raw_cooispi', 'raw_mb51', 'raw_zrmm024', 'raw_zrsd002', 
                  'raw_zrsd004', 'raw_zrsd006', 'raw_zrfi005']
    
    for table in raw_tables:
        count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {count:,} rows")
    
    print("\n="*80)
    print("VALIDATION - FACT TABLES")
    print("="*80)
    
    fact_tables = ['fact_production', 'fact_billing', 'fact_delivery', 
                   'fact_ar_aging', 'fact_lead_time', 'fact_alerts']
    
    for table in fact_tables:
        count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {count:,} rows")
    
    session.close()
    
    print("\n✅ Restore completed!")

if __name__ == "__main__":
    asyncio.run(main())
