"""
Count how many NEW rows would be inserted vs skipped
"""
import pandas as pd
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

# Load local file
file_path = Path('demodata/zrsd002.XLSX')
print(f"📄 Loading {file_path}...")

import openpyxl
wb = openpyxl.load_workbook(file_path)
ws = wb.active
headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
wb.close()

df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str, names=headers)
print(f"  Found {len(df)} total rows")
print(f"  Date range: {df['Billing Date'].min()} to {df['Billing Date'].max()}\n")

# Compute all hashes
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

print("🔄 Computing hashes for all rows...")
all_hashes = []
for idx, row in df.iterrows():
    raw_data = row_to_json(row)
    row_hash = compute_row_hash(raw_data)
    all_hashes.append(row_hash)

print(f"  ✓ Computed {len(all_hashes)} hashes\n")

# Get all hashes from production
print("🔍 Fetching all hashes from production...")
plink_path = r"C:\Program Files\PuTTY\plink.exe"

query = "SELECT row_hash FROM raw_zrsd002;"
cmd = f'docker exec alkana-postgres psql -U alkana_user -d alkana_dashboard -t -c "{query}"'

result = subprocess.run(
    [plink_path, "-pw", "it123", "-batch", "it@192.168.18.35", cmd],
    capture_output=True,
    text=True,
    timeout=60
)

production_hashes = set()
for line in result.stdout.strip().split('\n'):
    line = line.strip()
    if line and len(line) == 32:  # MD5 hash length
        production_hashes.add(line)

print(f"  ✓ Found {len(production_hashes)} hashes in production\n")

# Compare
local_hash_set = set(all_hashes)
existing_count = len(local_hash_set & production_hashes)
new_count = len(local_hash_set - production_hashes)

print("📊 RESULTS:")
print(f"  {'Total rows in local file:':<35} {len(df):>6}")
print(f"  {'Unique hashes in local file:':<35} {len(local_hash_set):>6}")
print(f"  {'Total hashes in production:':<35} {len(production_hashes):>6}")
print(f"  {'Rows that would be SKIPPED:':<35} {existing_count:>6} ({'(already exist)'})")
print(f"  {'Rows that would be INSERTED/UPDATED:':<35} {new_count:>6} {'(new or changed data)'}\n")

if new_count > 0:
    print("✅ CONCLUSION: File should insert/update", new_count, "rows")
    print("   If upload shows 'all skipped', there may be an issue with:")
    print("   - Hash computation differences between local and production")
    print("   - File encoding/parsing differences")
    print("   - Upload API not using correct file\n")
    
    # Show some new hashes
    new_hashes = list(local_hash_set - production_hashes)[:5]
    print(f" Sample NEW hashes (first 5):")
    for h in new_hashes:
        idx = all_hashes.index(h)
        row = df.iloc[idx]
        billing_doc = safe_str(row.get('Billing Document'))
        billing_date = row.get('Billing Date')
        print(f"     {h[:8]}... - Doc: {billing_doc}, Date: {billing_date}")
else:
    print("✅ CONCLUSION: ALL rows already exist in production")
    print("   This is EXPECTED behavior - system correctly skips duplicates")
    print("   No new data will be added when uploading this file")
