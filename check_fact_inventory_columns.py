import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='fact_inventory' ORDER BY ordinal_position")).fetchall()
print('Columns in fact_inventory:')
for r in result:
    print(f'  - {r[0]}')
db.close()
