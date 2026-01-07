from src.db.connection import SessionLocal
from src.db.models import RawMb51, FactLeadTime
from sqlalchemy import func
import pandas as pd

def analyze():
    print("=== ANALYZING STORAGE MOVEMENTS ===")
    db = SessionLocal()
    try:
        # 1. Check for Outbound MVT 601 (Goods Issue for Delivery)
        count_601 = db.query(RawMb51).filter(RawMb51.col_1_mvt_type == 601).count()
        print(f"Total MVT 601 (Delivery) records: {count_601}")
        
        if count_601 == 0:
            print("⚠ NO MVT 601 FOUND! Cannot calculate Storage Time without Outbound movements.")
            # Check what other movement types exist
            mvts = db.query(RawMb51.col_1_mvt_type, func.count(RawMb51.id))\
                .group_by(RawMb51.col_1_mvt_type).all()
            print("Available Movement Types:", mvts)
            return

        # 2. Check Match Rate (Batch 101 -> Batch 601)
        # Get Sample Batches from FactLeadTime
        sample_batches = db.query(FactLeadTime.batch)\
            .filter(FactLeadTime.batch.isnot(None))\
            .limit(20).all()
        
        batch_list = [b[0] for b in sample_batches]
        print(f"\nChecking 20 sample batches from FactLeadTime: {batch_list}")
        
        # Look for 601s for these batches
        matches = db.query(RawMb51.col_6_batch, RawMb51.col_0_posting_date)\
            .filter(RawMb51.col_1_mvt_type == 601)\
            .filter(RawMb51.col_6_batch.in_(batch_list))\
            .all()
            
        print(f"Found {len(matches)} outbound matches for these batches.")
        for b, d in matches:
            print(f"  - Batch {b} delivered on {d}")

    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze()
