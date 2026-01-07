from src.db.connection import engine
from sqlalchemy import text

result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total, 
        COUNT(CASE WHEN system_status LIKE '%%TECO%%' THEN 1 END) as completed 
    FROM fact_production
""")).fetchone()

print(f'Total: {result[0]}, Completed: {result[1]}')
