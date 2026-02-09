"""
Diagnose why ZRSD002 file gets all rows skipped in production
"""
import pandas as pd
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

# Load local file (same way as loader does)
file_path = Path('demodata/zrsd002.XLSX')
print(f"📄 Loading {file_path}...")

# Read headers from openpyxl (same as Zrsd002Loader)
import openpyxl
wb = openpyxl.load_workbook(file_path)
ws = wb.active
headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
wb.close()

# Read data starting from row 2
df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str, names=headers)
print(f"  Found {len(df)} rows, {len(df.columns)} columns")
print(f"  Date range: {df['Billing Date'].min()} to {df['Billing Date'].max()}")

# Compute row hashes (same logic as loader)
def safe_str(val):
    if pd.isna(val):
        return None
    return str(val).strip() if val else None

def row_to_json(row):
    result = {}
    for col in row.index:
        val = row[col]
        if pd.isna(val):
            result[str(col)] = None
        elif isinstance(val, datetime):
            result[str(col)] = val.isoformat()
        else:
            result[str(col)] = val
    return result

def compute_row_hash(row_dict):
    json_str = json.dumps(row_dict, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()

# Get sample hashes from local file
sample_hashes = []
sample_keys = []
for idx, row in df.head(10).iterrows():
    raw_data = row_to_json(row)
    row_hash = compute_row_hash(raw_data)
    billing_doc = safe_str(row.get('Billing Document'))
    billing_item = int(float(row.get('Billing Item'))) if row.get('Billing Item') else None
    
    sample_hashes.append(row_hash)
    sample_keys.append((billing_doc, billing_item))
    print(f"  Row {idx+1}: Doc={billing_doc}, Item={billing_item}, Hash={row_hash[:8]}")

print(f"\n🔍 Checking if these hashes exist in production...")

# Query production for these hashes
plink_path = r"C:\Program Files\PuTTY\plink.exe"

# Check first 5 hashes
hashes_str = "','".join(sample_hashes[:5])
query = f"SELECT row_hash, billing_document, billing_item, billing_date FROM raw_zrsd002 WHERE row_hash IN ('{hashes_str}');"

cmd = f'docker exec alkana-postgres psql -U alkana_user -d alkana_dashboard -c "{query}"'

result = subprocess.run(
    [plink_path, "-pw", "it123", "-batch", "it@192.168.18.35", cmd],
    capture_output=True,
    text=True,
    timeout=30
)

print(f"\n📊 Production matches:")
print(result.stdout)

if result.stderr:
    print(f"Errors: {result.stderr}")

# Also check by business keys
print(f"\n🔍 Checking by business keys (billing_document, billing_item)...")
for billing_doc, billing_item in sample_keys[:3]:
    query2 = f"SELECT billing_date, billing_document, billing_item, LEFT(row_hash, 8) as hash FROM raw_zrsd002 WHERE billing_document = '{billing_doc}' AND billing_item = {billing_item};"
    
    cmd2 = f'docker exec alkana-postgres psql -U alkana_user -d alkana_dashboard -c "{query2}"'
    
    result2 = subprocess.run(
        [plink_path, "-pw", "it123", "-batch", "it@192.168.18.35", cmd2],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(f"\n  Doc {billing_doc}, Item {billing_item}:")
    print(result2.stdout)

# Check billing dates in production
print(f"\n🔍 Checking date range in production for Feb 2026...")
date_query = "SELECT MIN(billing_date), MAX(billing_date), COUNT(*) FROM raw_zrsd002 WHERE billing_date >= '2026-02-01' AND billing_date < '2026-03-01';"

cmd3 = f'docker exec alkana-postgres psql -U alkana_user -d alkana_dashboard -c "{date_query}"'

result3 = subprocess.run(
    [plink_path, "-pw", "it123", "-batch", "it@192.168.18.35", cmd3],
    capture_output=True,
    text=True,
    timeout=30
)

print(result3.stdout)

print(f"\n💡 Analysis:")
print(f"  - Local file: {len(df)} rows dated {df['Billing Date'].min()} to {df['Billing Date'].max()}")
print(f"  - If hashes match in production → rows will be SKIPPED (data already exists)")
print(f"  - If business keys exist but hashes differ → rows will be UPDATED")
print(f"  - If neither exists → rows will be INSERTED")
