import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

# Check what columns raw_zrsd006 actually has with data
print("Checking raw_zrsd006 structure and data...")
print("=" * 70)

result = engine.connect().execute(text("""
    SELECT 
        material, material_desc, dist_channel,
        COUNT(*) OVER() as total_count
    FROM raw_zrsd006 
    WHERE material IS NOT NULL 
    LIMIT 5
""")).fetchall()

if result:
    print(f"✅ Found {result[0][3]} materials in raw_zrsd006")
    print("\nSample data:")
    for row in result[:5]:
        print(f"  Material: {row[0]}, Channel: {row[2]}, Desc: {row[1][:40]}...")
    
    # Now test JOIN
    print("\n" + "=" * 70)
    print("Testing JOIN with fact_production...")
    result2 = engine.connect().execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN rz.dist_channel IS NOT NULL THEN 1 END) as matched
        FROM fact_production fp
        LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
        WHERE fp.total_leadtime_days IS NOT NULL
    """)).fetchone()
    
    print(f"  Total orders: {result2[0]}")
    print(f"  Matched with channel: {result2[1]} ({result2[1]*100/result2[0]:.1f}%)")
    
    if result2[1] > 0:
        print("\n✅ SUCCESS! Can use raw_zrsd006 for distribution channel!")
    else:
        print("\n⚠️  No matches - need to check material code format")
else:
    print("❌ raw_zrsd006.material column is NULL or empty")
