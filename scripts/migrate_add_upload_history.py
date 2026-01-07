"""
Migration: Add upload_history table

Run with:
    python scripts/migrate_add_upload_history.py

Skills: database-operations
"""
import sys
sys.path.insert(0, '.')

from src.db.connection import engine
from src.db.models import Base, UploadHistory

print("=" * 60)
print("MIGRATION: Add upload_history table")
print("=" * 60)

# Create only the upload_history table
UploadHistory.__table__.create(engine, checkfirst=True)

print("✓ upload_history table created")
print()
print("Table structure:")
for column in UploadHistory.__table__.columns:
    print(f"  - {column.name}: {column.type}")

print()
print("=" * 60)
print("Migration completed successfully!")
print("=" * 60)
