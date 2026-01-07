import sys
sys.path.insert(0, '.')
from src.db.connection import engine
from sqlalchemy import text

print("Extracting data from JSONB with explicit commit...")

# Use connection with transaction
with engine.begin() as conn:
    # Check JSON structure first
    result = conn.execute(text("""
        SELECT raw_data FROM raw_zrsd006 LIMIT 1
    """)).fetchone()
    
    print(f"Sample JSON keys: {list(result[0].keys())[:10]}")
    
    # Update with correct JSON keys
    result = conn.execute(text("""
        UPDATE raw_zrsd006
        SET 
            material = (raw_data->>'Material Code')::text,
            material_desc = (raw_data->>'Mat. Description')::text
        WHERE raw_data IS NOT NULL
    """))
    
    print(f"Updated {result.rowcount} rows")
    # Transaction auto-commits when exiting 'with' block

# Verify
result = engine.connect().execute(text("""
    SELECT COUNT(material) FROM raw_zrsd006 WHERE material IS NOT NULL
""")).fetchone()

print(f"Verification: {result[0]} rows with material code")

# Test JOIN
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN rz.material IS NOT NULL THEN 1 END) as matched
    FROM fact_production fp
    LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
    WHERE fp.total_leadtime_days IS NOT NULL
""")).fetchone()

print(f"JOIN test: {result[1]}/{result[0]} matched ({result[1]*100/result[0]:.1f}%)")
