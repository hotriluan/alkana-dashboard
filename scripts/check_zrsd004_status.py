import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 80)
print("ZRSD004 DATA INTEGRITY CHECK (LOCAL)")
print("=" * 80)
print()

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check raw_zrsd004
    print("1️⃣ Checking raw_zrsd004 table...")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(delivery) as has_delivery,
            COUNT(material) as has_material,
            COUNT(ship_to_name) as has_ship_to_name,
            COUNT(material_desc) as has_material_desc,
            COUNT(dist_channel) as has_dist_channel
        FROM raw_zrsd004
    """))
    row = result.fetchone()
    
    total = row[0]
    print(f"   Total rows: {total:,}")
    
    if total > 0:
        print(f"   Delivery populated: {row[1]:,} ({row[1]/total*100:.1f}%)")
        print(f"   Material populated: {row[2]:,} ({row[2]/total*100:.1f}%)")
        print(f"   Ship-to Name populated: {row[3]:,} ({row[3]/total*100:.1f}%)")
        print(f"   Material Desc populated: {row[4]:,} ({row[4]/total*100:.1f}%)")
        print(f"   Dist Channel populated: {row[5]:,} ({row[5]/total*100:.1f}%)")
        
        # Check for 'Unnamed' columns (sign of header parsing failure)
        print()
        print("2️⃣ Checking for header parsing issues...")
        result2 = conn.execute(text("""
            SELECT raw_data
            FROM raw_zrsd004
            LIMIT 1
        """))
        sample = result2.fetchone()
        if sample and sample[0]:
            raw_keys = list(sample[0].keys())
            unnamed_count = sum(1 for k in raw_keys if 'Unnamed' in str(k))
            
            if unnamed_count > 0:
                print(f"   ❌ Found {unnamed_count} 'Unnamed' columns in raw_data!")
                print(f"   Sample keys: {raw_keys[:5]}")
            else:
                print(f"   ✅ No 'Unnamed' columns found")
                print(f"   Sample keys: {raw_keys[:5]}")
        else:
            print("   ⚠ No raw_data to check")
        
        # Sample data
        print()
        print("3️⃣ Sample data (first 3 rows)...")
        result3 = conn.execute(text("""
            SELECT delivery, material, ship_to_name, material_desc, dist_channel
            FROM raw_zrsd004
            LIMIT 3
        """))
        for i, row in enumerate(result3, 1):
            print(f"   Row {i}: delivery={row[0]}, material={row[1][:15] if row[1] else 'NULL'}, "
                  f"name={row[2][:20] if row[2] else 'NULL'}")
    else:
        print("   ⚠ No data in raw_zrsd004")
    
    # Check fact_delivery
    print()
    print("4️⃣ Checking fact_delivery table...")
    result4 = conn.execute(text("""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(delivery) as has_delivery,
            COUNT(material_code) as has_material_code,
            COUNT(ship_to_name) as has_ship_to_name,
            COUNT(material_description) as has_material_desc
        FROM fact_delivery
    """))
    row = result4.fetchone()
    
    total_fact = row[0]
    print(f"   Total rows: {total_fact:,}")
    
    if total_fact > 0:
        print(f"   Delivery populated: {row[1]:,} ({row[1]/total_fact*100:.1f}%)")
        print(f"   Material Code populated: {row[2]:,} ({row[2]/total_fact*100:.1f}%)")
        print(f"   Ship-to Name populated: {row[3]:,} ({row[3]/total_fact*100:.1f}%)")
        print(f"   Material Desc populated: {row[4]:,} ({row[4]/total_fact*100:.1f}%)")
    else:
        print("   ⚠ No data in fact_delivery")

print()
print("=" * 80)

# Overall assessment
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM raw_zrsd004 WHERE delivery IS NOT NULL"))
    valid_count = result.fetchone()[0]
    result = conn.execute(text("SELECT COUNT(*) FROM raw_zrsd004"))
    total_count = result.fetchone()[0]
    
    if total_count == 0:
        print("❌ STATUS: NO DATA - Need to upload zrsd004.XLSX")
    elif valid_count == 0:
        print("❌ STATUS: COMPLETE DATA LOSS - Loader has header parsing issue")
    elif valid_count / total_count < 0.95:
        print(f"⚠ STATUS: PARTIAL DATA LOSS - Only {valid_count/total_count*100:.1f}% valid")
    else:
        print(f"✅ STATUS: HEALTHY - {valid_count/total_count*100:.1f}% data populated")
print("=" * 80)
