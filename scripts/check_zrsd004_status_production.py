import subprocess
import json

print("=" * 80)
print("ZRSD004 DATA INTEGRITY CHECK (PRODUCTION)")
print("=" * 80)
print()

# Production database connection
PROD_HOST = "192.168.18.35"
PROD_DB = "alkana_dashboard"
PROD_USER = "postgres"
PROD_PASS = "password123"

# SSH credentials
SSH_USER = "it"
SSH_PASS = "it123"

def run_sql_on_production(sql_query):
    """Execute SQL on production database via SSH + Docker"""
    # Escape single quotes in SQL
    escaped_sql = sql_query.replace("'", "'\\''")
    
    # Build docker exec command for PostgreSQL (use alkana_user, not postgres)
    docker_cmd = f"docker exec -i alkana-postgres psql -U alkana_user -d alkana_dashboard -t -A -F',' -c \"{escaped_sql}\""
    
    # Execute via plink
    plink_cmd = [
        "plink",
        "-batch",
        "-pw", SSH_PASS,
        f"{SSH_USER}@{PROD_HOST}",
        docker_cmd
    ]
    
    result = subprocess.run(plink_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    return result.stdout.strip()

# Check raw_zrsd004
print("1️⃣ Checking raw_zrsd004 table...")
result = run_sql_on_production("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(delivery) as has_delivery,
        COUNT(material) as has_material,
        COUNT(ship_to_name) as has_ship_to_name,
        COUNT(material_desc) as has_material_desc,
        COUNT(dist_channel) as has_dist_channel
    FROM raw_zrsd004
""")

if result:
    parts = result.split(',')
    total = int(parts[0])
    print(f"   Total rows: {total:,}")
    
    if total > 0:
        print(f"   Delivery populated: {parts[1]} ({int(parts[1])/total*100:.1f}%)")
        print(f"   Material populated: {parts[2]} ({int(parts[2])/total*100:.1f}%)")
        print(f"   Ship-to Name populated: {parts[3]} ({int(parts[3])/total*100:.1f}%)")
        print(f"   Material Desc populated: {parts[4]} ({int(parts[4])/total*100:.1f}%)")
        print(f"   Dist Channel populated: {parts[5]} ({int(parts[5])/total*100:.1f}%)")
    else:
        print("   ⚠ No data in raw_zrsd004")

# Check for 'Unnamed' columns
print()
print("2️⃣ Checking for header parsing issues...")
result2 = run_sql_on_production("""
    SELECT raw_data::text
    FROM raw_zrsd004
    LIMIT 1
""")

if result2:
    if 'Unnamed' in result2:
        print("   ❌ Found 'Unnamed' columns in raw_data!")
    else:
        print("   ✅ No 'Unnamed' columns found")

# Sample data
print()
print("3️⃣ Sample data (first 3 rows)...")
result3 = run_sql_on_production("""
    SELECT delivery, material, ship_to_name
    FROM raw_zrsd004
    LIMIT 3
""")

if result3:
    for i, line in enumerate(result3.split('\n')[:3], 1):
        parts = line.split(',')
        if len(parts) >= 3:
            delivery = parts[0]
            material = parts[1][:15] if len(parts[1]) > 15 else parts[1]
            name = parts[2][:20] if len(parts[2]) > 20 else parts[2]
            print(f"   Row {i}: delivery={delivery}, material={material}, name={name}")

# Check fact_delivery
print()
print("4️⃣ Checking fact_delivery table...")
result4 = run_sql_on_production("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(delivery) as has_delivery,
        COUNT(material_code) as has_material_code,
        COUNT(ship_to_name) as has_ship_to_name,
        COUNT(material_description) as has_material_desc
    FROM fact_delivery
""")

if result4:
    parts = result4.split(',')
    total_fact = int(parts[0])
    print(f"   Total rows: {total_fact:,}")
    
    if total_fact > 0:
        print(f"   Delivery populated: {parts[1]} ({int(parts[1])/total_fact*100:.1f}%)")
        print(f"   Material Code populated: {parts[2]} ({int(parts[2])/total_fact*100:.1f}%)")
        print(f"   Ship-to Name populated: {parts[3]} ({int(parts[3])/total_fact*100:.1f}%)")
        print(f"   Material Desc populated: {parts[4]} ({int(parts[4])/total_fact*100:.1f}%)")
    else:
        print("   ⚠ No data in fact_delivery")

print()
print("=" * 80)

# Overall assessment
result_final = run_sql_on_production("SELECT COUNT(*) FROM raw_zrsd004 WHERE delivery IS NOT NULL")
if result_final:
    valid_count = int(result_final)
    result_total = run_sql_on_production("SELECT COUNT(*) FROM raw_zrsd004")
    total_count = int(result_total)
    
    if total_count == 0:
        print("❌ STATUS: NO DATA - Need to upload zrsd004.XLSX")
    elif valid_count == 0:
        print("❌ STATUS: COMPLETE DATA LOSS - Loader has header parsing issue")
    elif valid_count / total_count < 0.95:
        print(f"⚠ STATUS: PARTIAL DATA LOSS - Only {valid_count/total_count*100:.1f}% valid")
    else:
        print(f"✅ STATUS: HEALTHY - {valid_count/total_count*100:.1f}% data populated")
print("=" * 80)
