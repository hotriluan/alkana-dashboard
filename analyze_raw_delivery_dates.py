from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Create database session
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Import after loading env
import sys
sys.path.append('src')
from db.models import RawZrsd004

db = SessionLocal()

print("=" * 80)
print("🔍 ANALYZING RAW_ZRSD004 DELIVERY_DATE PATTERNS")
print("=" * 80)

# Count records with NULL vs non-NULL delivery_date
total = db.query(RawZrsd004).count()
with_date = db.query(RawZrsd004).filter(RawZrsd004.delivery_date.isnot(None)).count()
without_date = total - with_date

print(f"\n📊 OVERALL STATISTICS:")
print(f"  Total records: {total:,}")
print(f"  With delivery_date: {with_date:,} ({with_date/total*100:.1f}%)")
print(f"  WITHOUT delivery_date (NULL): {without_date:,} ({without_date/total*100:.1f}%)")

# Sample deliveries WITH dates
print(f"\n✅ SAMPLE DELIVERIES WITH DATES:")
with_dates = db.query(RawZrsd004).filter(RawZrsd004.delivery_date.isnot(None)).limit(5).all()
for rec in with_dates:
    print(f"  Delivery {rec.delivery}, Line {rec.line_item}: delivery_date = {rec.delivery_date}")

# Sample deliveries WITHOUT dates
print(f"\n❌ SAMPLE DELIVERIES WITHOUT DATES:")
without_dates = db.query(RawZrsd004).filter(RawZrsd004.delivery_date.is_(None)).limit(10).all()
for rec in without_dates:
    print(f"  Delivery {rec.delivery}, Line {rec.line_item}: delivery_date = NULL, actual_gi_date = {rec.actual_gi_date}")

# Check our specific problematic deliveries
print(f"\n🔎 CHECKING SPECIFIC DELIVERIES:")
for delivery_num in ['1910053734', '1910053733', '1910053732']:
    records = db.query(RawZrsd004).filter(RawZrsd004.delivery == delivery_num).all()
    if records:
        print(f"\n  Delivery {delivery_num}: {len(records)} records")
        for rec in records:
            print(f"    Line {rec.line_item}: delivery_date = {rec.delivery_date}, actual = {rec.actual_gi_date}")
    else:
        print(f"\n  Delivery {delivery_num}: NOT FOUND in database")

db.close()
