"""Check if V2 tables exist - Phase 0 verification"""
from src.db.connection import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename IN ('raw_zrpp062', 'fact_production_performance_v2')
    """))
    existing = [row[0] for row in result]
    
    if existing:
        print(f"⚠️ WARNING: Tables already exist: {existing}")
    else:
        print("✅ Namespace clear - no conflicting tables found")
