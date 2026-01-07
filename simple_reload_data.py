"""
SIMPLIFIED DATA RELOAD - No unicode emojis for Windows compatibility
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import sys

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

async def main():
    print("\n" + "="*80)
    print("  STEP 1: RE-LOADING RAW DATA")
    print("="*80 + "\n")
    
    sys.path.insert(0, 'src')
    from src.etl.loaders import load_all_raw_data
    from src.etl.transform import Transformer
    
    session = Session()
    
    try:
        # Step 1: Re-load raw data
        print("Loading from Excel files...")
        results = load_all_raw_data(session)
        
        print("\n" + "="*80)
        print("  LOAD RESULTS:")
        print("="*80)
        total_loaded = 0
        for table, stats in results.items():
            loaded = stats.get('loaded', 0)
            errors = stats.get('errors', 0)
            total_loaded += loaded
            print(f"  {table}: {loaded:,} rows loaded ({errors:,} errors)")
        
        print(f"\nTOTAL LOADED: {total_loaded:,} rows")
        
        # Step 2: Transform
        print("\n" + "="*80)
        print("  STEP 2: TRANSFORMING TO FACT TABLES")
        print("="*80 + "\n")
        
        transformer = Transformer(session)
        transformer.transform_all()
        
        # Step 3: Validate
        print("\n" + "="*80)
        print("  FINAL VALIDATION")
        print("="*80 + "\n")
        
        # Check fact_billing
        result = session.execute(text("""
            SELECT 
                COUNT(*) as rows,
                COUNT(DISTINCT billing_document) as docs,
                SUM(net_value)/1000000000 as revenue_b,
                COUNT(DISTINCT customer_name) as customers
            FROM fact_billing
        """)).fetchone()
        
        print(f"FACT_BILLING:")
        print(f"  Rows: {result[0]:,}")
        print(f"  Documents: {result[1]:,}")
        print(f"  Revenue: {result[2]:.2f}B VND")
        print(f"  Customers: {result[3]:,}")
        
        print("\n" + "="*80)
        print("  RELOAD COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
