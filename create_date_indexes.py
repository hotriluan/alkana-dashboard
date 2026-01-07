"""
CLAUDE KIT: Phase 5 Fix - Create date indexes manually
Skills: Database, SQL, Performance Optimization
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:password123@localhost:5432/alkana_dashboard"
engine = create_engine(DATABASE_URL)

print("=" * 70)
print("CLAUDE KIT: Phase 5 - Performance Indexes (Manual)")
print("Skills: Database, SQL Performance")
print("=" * 70)

indexes = [
    ("idx_fact_p02_p01_yield_production_date", "fact_p02_p01_yield", "production_date"),
    ("idx_fact_inventory_posting_date", "fact_inventory", "posting_date"),
    ("idx_fact_ar_aging_report_date", "fact_ar_aging", "report_date"),
    ("idx_fact_billing_billing_date", "fact_billing", "billing_date"),
]

with engine.begin() as conn:
    for idx_name, table_name, column_name in indexes:
        try:
            # Check if index exists
            check = conn.execute(text(f"""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = '{idx_name}'
            """)).fetchone()
            
            if check:
                print(f"  ⏭ {idx_name} - Already exists")
                continue
            
            # Create index
            print(f"  Creating {idx_name}...")
            conn.execute(text(f"""
                CREATE INDEX {idx_name} 
                ON {table_name}({column_name})
            """))
            print(f"  ✅ {idx_name} - Created")
            
        except Exception as e:
            print(f"  ❌ {idx_name} - Error: {str(e)[:100]}")

print("\n" + "=" * 70)
print("✅ Phase 5 Complete - Indexes Added")
print("=" * 70)

# Verify
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT tablename, indexname 
        FROM pg_indexes 
        WHERE tablename LIKE 'fact_%' 
        AND indexname LIKE 'idx_%date%'
        ORDER BY tablename, indexname
    """)).fetchall()
    
    print(f"\nDate indexes on fact tables: {len(result)}")
    for row in result:
        print(f"  {row[0]}.{row[1]}")
