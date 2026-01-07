import pandas as pd
from src.db.connection import SessionLocal
from sqlalchemy import text

# Load MB51
mb51_df = pd.read_excel('demodata/mb51.XLSX')

# Check P01 batch
p01_batch = '25L2535010'

print(f"=== P01 BATCH {p01_batch} ===\n")

p01_data = mb51_df[mb51_df['Batch'] == p01_batch]

for idx, row in p01_data.iterrows():
    if row['Movement Type'] == 101 and row['Plant'] == 1401:
        print(f"MVT {row['Movement Type']} @ Plant {row['Plant']}")
        print(f"  Material: {row['Material Description']} ({row['Material']})")
        print(f"  Qty: {row['Qty in Un. of Entry']} {row['Unit of Entry']}")
        print()

# Check UOM conversion in database
db = SessionLocal()

try:
    print("=== UOM CONVERSION CHECK ===\n")
    
    # Get P01 material code
    p01_material = '100006497'  # UFM-930 LIGHT GREY VN-6K
    
    uom_data = db.execute(text("""
        SELECT material_code, uom, kg_per_unit, source
        FROM dim_uom_conversion
        WHERE material_code = :material
    """), {"material": p01_material}).fetchall()
    
    if uom_data:
        for row in uom_data:
            print(f"Material: {row[0]}")
            print(f"  UOM: {row[1]}")
            print(f"  KG per unit: {row[2]}")
            print(f"  Source: {row[3]}")
    else:
        print(f"No UOM conversion found for {p01_material}")
    
    # Check in fact_p02_p01_yield
    print("\n=== FACT_P02_P01_YIELD DATA ===\n")
    
    yield_data = db.execute(text("""
        SELECT 
            p02_batch,
            p01_batch,
            p02_consumed_kg,
            p01_produced_kg,
            yield_pct
        FROM fact_p02_p01_yield
        WHERE p02_batch = '25L2535110'
    """)).fetchone()
    
    if yield_data:
        print(f"P02 Batch: {yield_data[0]}")
        print(f"P01 Batch: {yield_data[1]}")
        print(f"P02 Consumed: {yield_data[2]} KG")
        print(f"P01 Produced: {yield_data[3]} KG")
        print(f"Yield: {yield_data[4]}%")
        
        print(f"\nCalculation:")
        print(f"  {yield_data[3]} / {yield_data[2]} * 100 = {yield_data[4]}%")
        
        # Check if 24 PC was converted correctly
        print(f"\n24 PC should be converted to: {yield_data[3]} KG")
        print(f"  KG per PC = {yield_data[3] / 24:.2f}")
    
finally:
    db.close()
