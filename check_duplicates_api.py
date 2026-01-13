#!/usr/bin/env python3
"""Check for duplicates in raw_zrsd006 using Flask API"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Query to check duplicates
queries = [
    {
        "name": "Total records",
        "query": "SELECT COUNT(*) FROM raw_zrsd006"
    },
    {
        "name": "Unique row_hashes",
        "query": "SELECT COUNT(DISTINCT row_hash) FROM raw_zrsd006"
    },
    {
        "name": "Duplicate business keys",
        "query": """
            SELECT material, dist_channel, COUNT(*) as count
            FROM raw_zrsd006
            GROUP BY material, dist_channel
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 20
        """
    },
    {
        "name": "Unique materials and channels",
        "query": """
            SELECT 
                COUNT(DISTINCT material) as unique_materials,
                COUNT(DISTINCT dist_channel) as unique_channels
            FROM raw_zrsd006
        """
    }
]

print("📊 Checking raw_zrsd006 for duplicates...\n")

# Since we don't have a direct query endpoint, let's check using upload history
response = requests.get(f"{BASE_URL}/api/v1/upload/history?limit=100")
if response.status_code == 200:
    uploads = response.json()
    print(f"Total uploads: {len(uploads)}\n")
    
    # Group by file_type
    from collections import defaultdict
    by_type = defaultdict(list)
    
    for upload in uploads:
        by_type[upload.get('file_type', 'unknown')].append(upload)
    
    for file_type in sorted(by_type.keys()):
        entries = by_type[file_type]
        print(f"{file_type}:")
        for entry in entries[:5]:  # Show first 5
            rows_loaded = entry.get('rows_loaded', 0)
            rows_skipped = entry.get('rows_skipped', 0)
            rows_failed = entry.get('rows_failed', 0)
            print(f"  - {entry.get('original_name', 'N/A')}: Loaded={rows_loaded}, Skipped={rows_skipped}, Failed={rows_failed}")
        if len(entries) > 5:
            print(f"  ... and {len(entries) - 5} more")
        print()
else:
    print(f"Error: {response.status_code}")
