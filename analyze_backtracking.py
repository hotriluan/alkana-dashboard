from src.db.connection import SessionLocal
from src.db.models import RawMb51, FactPurchaseOrder, FactProduction
from sqlalchemy import and_
import pandas as pd

def analyze_backtracking():
    print("=== ANALYZING BACKTRACKING LOGIC (Batch -> PO 44xx -> PO Date) ===")
    db = SessionLocal()
    try:
        # 1. Find Mvt 101 records where PO starts with "44"
        # col_15_purchase_order is the PO column
        print("Searching for Mvt 101 with PO starting with '44'...")
        
        backtrack_candidates = db.query(RawMb51.col_6_batch, RawMb51.col_15_purchase_order)\
            .filter(RawMb51.col_1_mvt_type == 101)\
            .filter(RawMb51.col_15_purchase_order.like('44%'))\
            .limit(20).all()
            
        print(f"Found {len(backtrack_candidates)} candidate records in RawMb51.")
        
        if not backtrack_candidates:
            print("⚠ NO Candidates found! Checking raw values in col_15 for 101...")
            sample = db.query(RawMb51.col_15_purchase_order).filter(RawMb51.col_1_mvt_type == 101).limit(10).all()
            print("Sample POs in 101:", sample)
            return

        batch_po_map = {b: p for b, p in backtrack_candidates if b and p}
        po_list = list(batch_po_map.values())
        print(f"Sample Batches/POs: {list(batch_po_map.items())[:5]}")
        
        # 2. Look up Dates in FactPurchaseOrder
        print(f"\nLooking up {len(po_list)} POs in FactPurchaseOrder...")
        po_dates = db.query(FactPurchaseOrder.purch_order, FactPurchaseOrder.purch_date)\
            .filter(FactPurchaseOrder.purch_order.in_(po_list))\
            .all()
            
        po_date_map = {p: d for p, d in po_dates}
        print(f"Found {len(po_date_map)} matching PO Dates.")
        
        # 3. Simulate Prep Time Calc (Release Date - PO Date)
        # Find Production Orders for these batches
        batches = list(batch_po_map.keys())
        prod_orders = db.query(FactProduction.batch, FactProduction.release_date)\
            .filter(FactProduction.batch.in_(batches))\
            .all()
            
        print("\n--- Simulated Preparation Times ---")
        for batch, release_date in prod_orders:
            po_num = batch_po_map.get(batch)
            if po_num and po_num in po_date_map:
                po_date = po_date_map[po_num]
                if release_date and po_date:
                    prep_days = (release_date - po_date).days
                    print(f"Batch {batch}: PO {po_num} ({po_date}) -> Release {release_date} | Prep = {prep_days} days")
                else:
                     print(f"Batch {batch}: Date missing")
            else:
                print(f"Batch {batch}: PO Date not found")

    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze_backtracking()
