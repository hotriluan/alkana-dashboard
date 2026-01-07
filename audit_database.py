"""
COMPREHENSIVE DATABASE AUDIT - Check for zrsd006 related tables and data
Skills: database-analysis, backend-development
"""
import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text, inspect

print("=" * 80)
print("DATABASE AUDIT: Checking for zrsd006-related tables and distribution channel data")
print("=" * 80)

# 1. List ALL tables in database
print("\n1. ALL TABLES IN DATABASE:")
print("-" * 80)
inspector = inspect(engine)
all_tables = inspector.get_table_names()
print(f"Total tables: {len(all_tables)}\n")

# Categorize tables
raw_tables = [t for t in all_tables if t.startswith('raw_')]
fact_tables = [t for t in all_tables if t.startswith('fact_')]
dim_tables = [t for t in all_tables if t.startswith('dim_')]
other_tables = [t for t in all_tables if not (t.startswith('raw_') or t.startswith('fact_') or t.startswith('dim_'))]

print(f"RAW tables ({len(raw_tables)}):")
for t in sorted(raw_tables):
    print(f"  - {t}")

print(f"\nFACT tables ({len(fact_tables)}):")
for t in sorted(fact_tables):
    print(f"  - {t}")

print(f"\nDIM tables ({len(dim_tables)}):")
for t in sorted(dim_tables):
    print(f"  - {t}")

if other_tables:
    print(f"\nOTHER tables ({len(other_tables)}):")
    for t in sorted(other_tables):
        print(f"  - {t}")

# 2. Check raw_zrsd006 specifically
print("\n" + "=" * 80)
print("2. CHECKING raw_zrsd006 TABLE:")
print("-" * 80)
if 'raw_zrsd006' in all_tables:
    # Get row count
    result = engine.connect().execute(text("SELECT COUNT(*) FROM raw_zrsd006")).fetchone()
    row_count = result[0]
    print(f"✅ Table EXISTS")
    print(f"   Total rows: {row_count}")
    
    if row_count > 0:
        # Check columns with data
        columns = inspector.get_columns('raw_zrsd006')
        print(f"   Columns: {len(columns)}")
        
        # Check key columns
        result = engine.connect().execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(material) as material_count,
                COUNT(dist_channel) as channel_count,
                COUNT(material_desc) as desc_count
            FROM raw_zrsd006
        """)).fetchone()
        
        print(f"\n   Data population:")
        print(f"     - material: {result[1]}/{result[0]} ({result[1]*100/result[0]:.1f}%)")
        print(f"     - dist_channel: {result[2]}/{result[0]} ({result[2]*100/result[0]:.1f}%)")
        print(f"     - material_desc: {result[3]}/{result[0]} ({result[3]*100/result[0]:.1f}%)")
        
        if result[2] > 0:
            # Show distribution channel breakdown
            result2 = engine.connect().execute(text("""
                SELECT dist_channel, COUNT(*) 
                FROM raw_zrsd006 
                WHERE dist_channel IS NOT NULL
                GROUP BY dist_channel 
                ORDER BY dist_channel
            """)).fetchall()
            print(f"\n   Distribution channels:")
            for row in result2:
                print(f"     - {row[0]}: {row[1]} materials")
    else:
        print("   ⚠️  Table is EMPTY")
else:
    print("❌ Table does NOT exist")

# 3. Check dim_material
print("\n" + "=" * 80)
print("3. CHECKING dim_material TABLE:")
print("-" * 80)
if 'dim_material' in all_tables:
    result = engine.connect().execute(text("SELECT COUNT(*) FROM dim_material")).fetchone()
    row_count = result[0]
    print(f"✅ Table EXISTS")
    print(f"   Total rows: {row_count}")
    
    if row_count > 0:
        # Check for dist_channel column
        columns = [c['name'] for c in inspector.get_columns('dim_material')]
        if 'dist_channel' in columns:
            result = engine.connect().execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(dist_channel) as channel_count
                FROM dim_material
            """)).fetchone()
            print(f"   dist_channel column: EXISTS")
            print(f"   Data: {result[1]}/{result[0]} ({result[1]*100/result[0]:.1f}%)")
            
            if result[1] > 0:
                result2 = engine.connect().execute(text("""
                    SELECT dist_channel, COUNT(*) 
                    FROM dim_material 
                    WHERE dist_channel IS NOT NULL
                    GROUP BY dist_channel 
                    ORDER BY dist_channel
                """)).fetchall()
                print(f"\n   Distribution channels:")
                for row in result2:
                    print(f"     - {row[0]}: {row[1]} materials")
        else:
            print(f"   ❌ dist_channel column does NOT exist")
            print(f"   Available columns: {', '.join(columns[:10])}...")
    else:
        print("   ⚠️  Table is EMPTY")
else:
    print("❌ Table does NOT exist")

# 4. Search for ANY table with distribution channel data
print("\n" + "=" * 80)
print("4. SEARCHING ALL TABLES FOR 'dist_channel' OR 'distribution_channel' COLUMNS:")
print("-" * 80)
tables_with_channel = []
for table in all_tables:
    columns = [c['name'] for c in inspector.get_columns(table)]
    if any('dist' in col.lower() and 'channel' in col.lower() for col in columns):
        # Check if has data
        channel_col = [c for c in columns if 'dist' in c.lower() and 'channel' in c.lower()][0]
        result = engine.connect().execute(text(f"SELECT COUNT({channel_col}) FROM {table} WHERE {channel_col} IS NOT NULL")).fetchone()
        if result[0] > 0:
            tables_with_channel.append((table, channel_col, result[0]))
            print(f"✅ {table}.{channel_col}: {result[0]} rows with data")

if not tables_with_channel:
    print("❌ NO tables found with distribution channel data")

# 5. Check material-related tables
print("\n" + "=" * 80)
print("5. CHECKING MATERIAL-RELATED TABLES:")
print("-" * 80)
material_tables = [t for t in all_tables if 'material' in t.lower() or 'product' in t.lower()]
for table in sorted(material_tables):
    result = engine.connect().execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
    columns = [c['name'] for c in inspector.get_columns(table)]
    mat_cols = [c for c in columns if 'material' in c.lower()]
    print(f"{table}: {result[0]} rows, material columns: {', '.join(mat_cols[:5])}")

# 6. Final recommendation
print("\n" + "=" * 80)
print("AUDIT SUMMARY & RECOMMENDATION:")
print("=" * 80)

if 'raw_zrsd006' in all_tables:
    result = engine.connect().execute(text("SELECT COUNT(dist_channel) FROM raw_zrsd006 WHERE dist_channel IS NOT NULL")).fetchone()
    if result[0] > 0:
        print("✅ raw_zrsd006 EXISTS and HAS distribution channel data")
        print("   → Can use raw_zrsd006 directly for JOIN")
    else:
        print("⚠️  raw_zrsd006 EXISTS but NO distribution channel data")
        print("   → Need to import zrsd006.XLSX")
else:
    print("❌ raw_zrsd006 does NOT exist")
    print("   → Need to create table and import zrsd006.XLSX")

if tables_with_channel:
    print(f"\n✅ Found {len(tables_with_channel)} other table(s) with distribution channel:")
    for t, col, count in tables_with_channel:
        print(f"   - {t}.{col}: {count} rows")
