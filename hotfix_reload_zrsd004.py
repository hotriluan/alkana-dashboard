"""
HOTFIX: Fix NULL delivery_date in raw_zrsd004 and fact_delivery

Root Cause:
- Old records loaded before delivery_date column existed have NULL values
- Upsert logic skips records when row_hash matches (hash doesn't include delivery_date)
- Need to delete NULL records and re-load from Excel

Solution:
1. Delete records with NULL delivery_date from raw_zrsd004
2. Re-load missing records from Excel (via upsert - they'll be treated as NEW)
3. Transform to fact_delivery
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import psycopg2
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("🔄 HOTFIX: FIXING NULL DELIVERY_DATE")
print("=" * 80)

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

try:
    # Step 1: Check raw_zrsd004 vs Excel
    print("\n📌 Step 1: Comparing raw_zrsd004 vs Excel...")
    
    cur.execute("SELECT COUNT(*) FROM raw_zrsd004")
    db_count = cur.fetchone()[0]
    print(f"  Database records: {db_count:,}")
    
    # Count Excel records
    import pandas as pd
    excel_path = Path('demodata/zrsd004.XLSX')
    df_check = pd.read_excel(excel_path, header=0, nrows=0)
    df_full = pd.read_excel(excel_path, header=0)
    excel_count = len(df_full)
    print(f"  Excel records: {excel_count:,}")
    print(f"  Missing in DB: {excel_count - db_count:,}")
    
    if db_count >= excel_count:
        print(f"  ✅ Database has all records from Excel!")
    
    # Step 2: Re-load from Excel to fill gaps
    print(f"\n📌 Step 2: Re-loading from Excel (upsert mode)...")
    
    from db.session import SessionLocal
    from etl.loaders import Zrsd004Loader
    
    db = SessionLocal()
    loader = Zrsd004Loader(db, mode='upsert', file_path=Path('demodata/zrsd004.XLSX'))
    stats = loader.load()
    db.close()
    
    print(f"  ✅ Loaded: {stats['loaded']:,}")
    print(f"  ✅ Updated: {stats['updated']:,}")
    print(f"  ⏭️ Skipped: {stats['skipped']:,}")
    if stats['errors']:
        print(f"  ⚠️ Errors: {len(stats['errors'])}")
        for error in stats['errors'][:5]:
            print(f"    - {error}")
    
    # Step 3: Transform to fact_delivery
    print("\n📌 Step 3: Transforming to fact_delivery...")
    
    from etl.transform import DataTransformer
    
    db = SessionLocal()
    transformer = DataTransformer(db)
    transformer.transform_zrsd004()
    db.close()
    print("  ✅ Transformation complete")
    
    # Step 4: Verify
    print("\n📌 Step 4: Verifying fix...")
    cur.execute("SELECT COUNT(*) FROM raw_zrsd004 WHERE delivery_date IS NULL")
    remaining_null = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM fact_delivery WHERE delivery_date IS NULL")
    fact_null = cur.fetchone()[0]
    
    print(f"\n  📊 RESULTS:")
    print(f"    raw_zrsd004 NULL records: {remaining_null:,}")
    print(f"    fact_delivery NULL records: {fact_null:,}")
    
    if remaining_null == 0:
        print(f"\n  ✅ SUCCESS! All raw_zrsd004 records now have delivery_date")
    else:
        print(f"\n  ⚠️ WARNING: Still {remaining_null:,} NULL records in raw_zrsd004")
    
    # Check specific deliveries
    print("\n  🔎 CHECKING SPECIFIC DELIVERIES:")
    for delivery_num in ['1910053734', '1910053733', '1910053732']:
        cur.execute(f"""
            SELECT line_item, delivery_date, actual_gi_date
            FROM fact_delivery
            WHERE delivery = '{delivery_num}'
            ORDER BY line_item
        """)
        records = cur.fetchall()
        if records:
            print(f"\n    Delivery {delivery_num}: {len(records)} records")
            for line_item, delivery_date, actual_gi_date in records:
                status = "✅" if delivery_date else "❌"
                print(f"      {status} Line {line_item}: delivery_date = {delivery_date}, actual = {actual_gi_date}")
    
    print("\n" + "=" * 80)
    print("✅ HOTFIX COMPLETE!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cur.close()
    conn.close()
