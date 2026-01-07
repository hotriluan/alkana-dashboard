from src.db.connection import SessionLocal
from src.db.models import RawZrsd006

db = SessionLocal()

try:
    # Check total records
    total = db.query(RawZrsd006).count()
    print(f"Total zrsd006 records: {total}")
    
    # Check dist_channel values
    with_channel = db.query(RawZrsd006).filter(RawZrsd006.dist_channel.isnot(None)).count()
    print(f"With dist_channel: {with_channel}")
    
    # Sample records
    samples = db.query(RawZrsd006).limit(10).all()
    print(f"\n=== SAMPLE RECORDS ===")
    for s in samples:
        print(f"Material: {s.material}, Channel: {s.dist_channel}")
        
finally:
    db.close()
