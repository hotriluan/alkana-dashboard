"""Execute MB51 Transform ONLY - Emergency Repair Script"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.etl.transform import Transformer

# Database connection
DATABASE_URL = "postgresql://postgres:password123@localhost:5432/alkana_dashboard"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

print("=" * 70)
print("🚑 EMERGENCY ETL REPAIR: MB51 Transform")
print("=" * 70)

db = SessionLocal()
try:
    transformer = Transformer(db)
    
    print("\n[STEP 1/2] Checking raw_mb51 status...")
    from sqlalchemy import text
    raw_count = db.execute(text("SELECT COUNT(*) FROM raw_mb51")).scalar()
    print(f"  ✓ raw_mb51 has {raw_count:,} rows")
    
    print("\n[STEP 2/2] Running transform_mb51()...")
    transformer.transform_mb51()
    
    print("\n" + "=" * 70)
    print("✅ TRANSFORMATION COMPLETE - Verifying...")
    print("=" * 70)
    
    # Verify results
    fact_count = db.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
    dim_count = db.execute(text("SELECT COUNT(*) FROM dim_material")).scalar()
    
    print(f"\n📊 Results:")
    print(f"  • dim_material: {dim_count:,} materials")
    print(f"  • fact_inventory: {fact_count:,} transactions")
    
    # Movement type distribution
    mvt_dist = db.execute(text("""
        SELECT mvt_type, COUNT(*) as count 
        FROM fact_inventory 
        GROUP BY mvt_type 
        ORDER BY count DESC 
        LIMIT 10
    """)).fetchall()
    
    print(f"\n📈 Movement Type Distribution (Top 10):")
    for mvt_type, count in mvt_dist:
        print(f"  • mvt_type {mvt_type}: {count:,} transactions")
    
    # Orphan check
    orphan_count = db.execute(text("""
        SELECT COUNT(*) 
        FROM fact_inventory fi 
        LEFT JOIN dim_material dm ON fi.material_code = dm.material_code 
        WHERE dm.material_code IS NULL
    """)).scalar()
    
    print(f"\n🔗 Orphan Check:")
    print(f"  • Orphaned materials: {orphan_count:,} (should be 0)")
    
    if fact_count > 100000 and orphan_count == 0:
        print("\n🎉 SUCCESS! ETL pipeline repaired.")
    else:
        print("\n⚠️ WARNING: Results look unusual. Review logs above.")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
