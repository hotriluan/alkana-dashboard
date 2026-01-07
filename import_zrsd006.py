"""
Import zrsd006.XLSX into raw_zrsd006 table
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from sqlalchemy import text
from src.db.connection import engine, get_db
from datetime import datetime

print("=" * 70)
print("IMPORTING ZRSD006.XLSX TO DATABASE")
print("=" * 70)

# Read Excel
print("\n1. Reading Excel file...")
df = pd.read_excel('demodata/zrsd006.XLSX')
print(f"   Loaded {len(df)} rows")

# Clean column names
df.columns = df.columns.str.strip()

# Map columns to database schema
print("\n2. Mapping columns...")
column_mapping = {
    'Material Code': 'material',
    'Mat. Description': 'material_desc',
    'Distribution Channel': 'dist_channel',
    'UOM': 'uom',
    'PH 1': 'ph1',
    'Division': 'ph1_desc',
    'PH 2': 'ph2',
    'Business': 'ph2_desc',
    'PH 3': 'ph3',
    'Sub Business': 'ph3_desc',
    'PH 4': 'ph4',
    'Product Group': 'ph4_desc',
    'PH 5': 'ph5',
    'Product Group 1': 'ph5_desc',
    'PH 6': 'ph6',
    'Product Group 2': 'ph6_desc',
    'PH 7': 'ph7',
    'Series': 'ph7_desc'
}

# Select and rename columns
df_import = df[list(column_mapping.keys())].copy()
df_import.columns = [column_mapping[col] for col in df_import.columns]

# Add metadata
df_import['source_file'] = 'zrsd006.XLSX'
df_import['source_row'] = range(1, len(df_import) + 1)
df_import['loaded_at'] = datetime.utcnow()

# Convert dist_channel to string
df_import['dist_channel'] = df_import['dist_channel'].astype(str)

print(f"   Columns mapped: {list(df_import.columns)}")
print(f"\n   Distribution channel breakdown:")
print(df_import['dist_channel'].value_counts())

# Clear existing data
print("\n3. Clearing existing raw_zrsd006 data...")
engine.connect().execute(text("TRUNCATE TABLE raw_zrsd006 RESTART IDENTITY CASCADE"))
print("   ✅ Table cleared")

# Import to database
print("\n4. Importing to database...")
df_import.to_sql('raw_zrsd006', engine, if_exists='append', index=False, method='multi', chunksize=1000)
print(f"   ✅ Imported {len(df_import)} rows")

# Verify
print("\n5. Verifying import...")
result = engine.connect().execute(text("""
    SELECT 
        dist_channel,
        COUNT(*) as count
    FROM raw_zrsd006
    WHERE material IS NOT NULL
    GROUP BY dist_channel
    ORDER BY dist_channel
""")).fetchall()

print("   Distribution channels in database:")
for row in result:
    channel_name = {
        '11': 'Industry',
        '12': 'Over Sea',
        '13': 'Retail',
        '15': 'Project'
    }.get(row[0], 'Other')
    print(f"     {row[0]} ({channel_name}): {row[1]} materials")

# Test JOIN with fact_production
print("\n6. Testing JOIN with fact_production...")
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN rz.dist_channel IS NOT NULL THEN 1 END) as matched,
        ROUND(COUNT(CASE WHEN rz.dist_channel IS NOT NULL THEN 1 END)*100.0/COUNT(*), 1) as pct
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()

print(f"   Total production orders: {result[0]}")
print(f"   Matched with channel: {result[1]} ({result[2]}%)")

if result[2] > 50:
    print("\n" + "=" * 70)
    print("✅ SUCCESS! zrsd006 data imported and ready to use!")
    print("=" * 70)
else:
    print("\n⚠️  Warning: Low match rate. May need to check material code format.")
