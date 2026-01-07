from src.db.connection import engine
from sqlalchemy import text

# Add channel_code column to fact_lead_time table
sql = text("""
ALTER TABLE fact_lead_time 
ADD COLUMN channel_code VARCHAR(10);
""")

try:
    with engine.connect() as conn:
        conn.execute(sql)
        conn.commit()
    print("[OK] Added channel_code column to fact_lead_time")
except Exception as e:
    print(f"[ERROR] {e}")
