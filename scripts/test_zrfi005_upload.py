"""Test ZRFI005 upload deduplication"""
from src.db.connection import get_db
from src.etl.loaders import Zrfi005Loader
from pathlib import Path
from datetime import date
from sqlalchemy import text

db = next(get_db())

# Check current count
before = db.execute(text("SELECT COUNT(*) FROM raw_zrfi005 WHERE snapshot_date = '2026-01-08'")).scalar()
print(f"Before upload: {before} records for 2026-01-08")

# Upload again (should UPDATE existing, not INSERT new)
file_path = Path('demodata/ZRFI005.XLSX')
loader = Zrfi005Loader(db, mode='upsert', file_path=file_path)
stats = loader.load(snapshot_date=date(2026, 1, 8))

print(f"\nUpload stats:")
print(f"  Loaded: {stats['loaded']}")
print(f"  Updated: {stats['updated']}")
print(f"  Skipped: {stats['skipped']}")
print(f"  Errors: {stats['errors']}")

# Check after count
after = db.execute(text("SELECT COUNT(*) FROM raw_zrfi005 WHERE snapshot_date = '2026-01-08'")).scalar()
print(f"\nAfter upload: {after} records for 2026-01-08")

if after == before:
    print("✅ SUCCESS: No duplicates created!")
elif stats['skipped'] == before:
    print("✅ SUCCESS: All records skipped (identical data)!")
else:
    print(f"❌ FAIL: Expected {before} records, got {after}")

db.close()
