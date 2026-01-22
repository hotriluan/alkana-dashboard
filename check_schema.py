from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:password123@localhost:5432/alkana_dashboard')
conn = engine.connect()
result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'fact_production' AND table_schema = 'public' ORDER BY column_name"))
print('\n'.join([r[0] for r in result]))
conn.close()
