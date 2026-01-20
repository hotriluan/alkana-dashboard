import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM raw_zrsd004 WHERE delivery_date IS NULL")
print(f"raw_zrsd004 NULL: {cur.fetchone()[0]:,}")

cur.execute("SELECT COUNT(*) FROM raw_zrsd004")
print(f"raw_zrsd004 Total: {cur.fetchone()[0]:,}")

cur.execute("SELECT COUNT(*) FROM fact_delivery WHERE delivery_date IS NULL")
print(f"fact_delivery NULL: {cur.fetchone()[0]:,}")

cur.execute("SELECT COUNT(*) FROM fact_delivery")
print(f"fact_delivery Total: {cur.fetchone()[0]:,}")

cur.close()
conn.close()
