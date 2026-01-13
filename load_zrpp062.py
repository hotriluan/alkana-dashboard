"""
Quick script to load ZRPP062 data into V2 tables
"""
from src.db.connection import SessionLocal
from src.etl.loaders import Zrpp062Loader

db = SessionLocal()
try:
    loader = Zrpp062Loader(db, mode='insert')
    stats = loader.load()
    print(f'✅ Loaded: {stats["loaded"]}, Updated: {stats["updated"]}, Errors: {stats["errors"]}')
except Exception as e:
    print(f'❌ Error: {e}')
finally:
    db.close()
