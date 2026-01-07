"""
Update raw_zrsd006: Extract data from raw_data JSONB to proper columns
"""
import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

print("=" * 70)
print("UPDATING raw_zrsd006: Extracting data from JSONB to columns")
print("=" * 70)

# 1. Check current state
print("\n1. Current state:")
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(material) as has_material_col,
        COUNT(raw_data->>'Material Code') as has_material_json
    FROM raw_zrsd006
""")).fetchone()
print(f"   Total rows: {result[0]}")
print(f"   material column populated: {result[1]}")
print(f"   Material Code in JSON: {result[2]}")

# 2. Update columns from JSONB
print("\n2. Extracting data from JSONB...")
engine.connect().execute(text("""
    UPDATE raw_zrsd006
    SET 
        material = raw_data->>'Material Code',
        material_desc = raw_data->>'Mat. Description',
        uom = raw_data->>'UOM',
        ph1 = raw_data->>'PH 1',
        ph1_desc = raw_data->>'Division',
        ph2 = raw_data->>'PH 2',
        ph2_desc = raw_data->>'Business',
        ph3 = raw_data->>'PH 3',
        ph3_desc = raw_data->>'Sub Business',
        ph4 = raw_data->>'PH 4',
        ph4_desc = raw_data->>'Product Group',
        ph5 = raw_data->>'PH 5',
        ph5_desc = raw_data->>'Product Group 1',
        ph6 = raw_data->>'PH 6',
        ph6_desc = raw_data->>'Product Group 2',
        ph7 = raw_data->>'PH 7',
        ph7_desc = raw_data->>'Series'
    WHERE raw_data IS NOT NULL
"""))
print("   ✅ Data extracted")

# 3. Verify
print("\n3. Verification:")
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(material) as has_material,
        COUNT(dist_channel) as has_channel
    FROM raw_zrsd006
""")).fetchone()
print(f"   Total: {result[0]}")
print(f"   With material: {result[1]} ({result[1]*100/result[0]:.1f}%)")
print(f"   With dist_channel: {result[2]} ({result[2]*100/result[0]:.1f}%)")

# 4. Test JOIN
print("\n4. Testing JOIN with fact_production:")
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN rz.dist_channel IS NOT NULL THEN 1 END) as matched,
        ROUND(COUNT(CASE WHEN rz.dist_channel IS NOT NULL THEN 1 END)*100.0/COUNT(*), 1) as pct
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()
print(f"   Total orders: {result[0]}")
print(f"   Matched with channel: {result[1]} ({result[2]}%)")

# 5. Show grouping
if result[2] > 0:
    print("\n5. Distribution by channel:")
    result = engine.connect().execute(text("""
        SELECT 
            COALESCE(rz.dist_channel, '99') as ch,
            CASE WHEN fp.is_mto THEN 'MTO' ELSE 'MTS' END as type,
            COUNT(*) as cnt,
            ROUND(AVG(fp.total_leadtime_days), 1) as avg_lt
        FROM fact_production fp
        LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
        WHERE fp.total_leadtime_days IS NOT NULL
        GROUP BY rz.dist_channel, fp.is_mto
        ORDER BY rz.dist_channel, fp.is_mto DESC
    """)).fetchall()
    
    for row in result:
        ch_name = {'11': 'Industry', '12': 'Over Sea', '13': 'Retail', '15': 'Project', '99': 'No Data'}.get(row[0], row[0])
        print(f"   {ch_name:<15s} {row[1]}: {row[2]:4d} orders, {row[3]:5.1f} days avg")

print("\n" + "=" * 70)
if result[2] >= 50:
    print("✅ SUCCESS! Ready to use raw_zrsd006 for distribution channel grouping!")
else:
    print(f"⚠️  Match rate: {result[2]}% - May need further investigation")
print("=" * 70)
