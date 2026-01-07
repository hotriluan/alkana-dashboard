import sys
sys.path.insert(0, 'C:\\dev\\alkana-dashboard')
from src.db.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='raw_zrsd004' ORDER BY ordinal_position")).fetchall()
print("Columns in raw_zrsd004:")
for r in result:
    print(f"  - {r[0]}")

# Quick data check
sample = db.execute(text("SELECT delivery, material, ship_to_name, ship_to_city FROM raw_zrsd004 LIMIT 3")).fetchall()
print("\nSample data:")
for row in sample:
    print(f"  Delivery: {row[0]}, Material: {row[1]}, Ship-to: {row[2]}, City: {row[3]}")

# NULL check
total = db.execute(text("SELECT COUNT(*) FROM raw_zrsd004")).scalar()
null_delivery = db.execute(text("SELECT COUNT(*) FROM raw_zrsd004 WHERE delivery IS NULL")).scalar()
null_material = db.execute(text("SELECT COUNT(*) FROM raw_zrsd004 WHERE material IS NULL")).scalar()

print(f"\nData Quality:")
print(f"  Total: {total:,}")
print(f"  NULL Deliveries: {null_delivery:,} ({null_delivery/total*100:.1f}%)")
print(f"  NULL Materials: {null_material:,} ({null_material/total*100:.1f}%)")

if null_delivery/total < 0.05:
    print("\n🎉 ✅ FIX VERIFIED - Data loaded successfully!")
else:
    print("\n❌ Still seeing NULL data")

db.close()
