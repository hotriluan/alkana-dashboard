from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("=== DIM_UOM_CONVERSION SCHEMA ===\n")
    
    # Get table schema
    schema = db.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'dim_uom_conversion'
        ORDER BY ordinal_position
    """)).fetchall()
    
    for col in schema:
        print(f"{col[0]}: {col[1]}")
    
    print("\n=== CHECK P01 MATERIAL UOM ===\n")
    
    # UFM-930 LIGHT GREY VN-6K
    p01_material = '100006497'
    
    uom_data = db.execute(text("""
        SELECT *
        FROM dim_uom_conversion
        WHERE material_code = :material
    """), {"material": p01_material}).fetchall()
    
    if uom_data:
        print(f"Found UOM data for {p01_material}:")
        for row in uom_data:
            print(f"  {row}")
    else:
        print(f"No UOM data for {p01_material}")
    
    # Check fact_p02_p01_yield for this batch
    print("\n=== YIELD DATA FOR BATCH 25L2535110 ===\n")
    
    yield_data = db.execute(text("""
        SELECT *
        FROM fact_p02_p01_yield
        WHERE p02_batch = '25L2535110'
    """)).fetchone()
    
    if yield_data:
        print(f"Data: {yield_data}")
    else:
        print("No yield data found")
    
    # Check raw MB51 data in database
    print("\n=== RAW MB51 FOR P01 BATCH 25L2535010 ===\n")
    
    mb51_data = db.execute(text("""
        SELECT 
            col_1_mvt_type,
            col_2_plant,
            col_4_material,
            col_5_material_desc,
            col_6_batch,
            col_7_qty,
            col_8_uom
        FROM raw_mb51
        WHERE col_6_batch = '25L2535010'
        AND col_1_mvt_type = 101
        AND col_2_plant = 1401
    """)).fetchall()
    
    for row in mb51_data:
        print(f"MVT {row[0]} @ Plant {row[1]}")
        print(f"  Material: {row[3]} ({row[2]})")
        print(f"  Batch: {row[4]}")
        print(f"  Qty: {row[5]} {row[6]}")
    
finally:
    db.close()
