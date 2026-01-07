from src.db.connection import SessionLocal
from src.db.models import FactProduction, FactBilling
import pandas as pd
from sqlalchemy import func

def analyze_prep_time():
    print("=== ANALYZING PREPARATION TIME POSSIBILITIES ===")
    db = SessionLocal()
    try:
        # 1. Get MTO Production Orders with Sales Orders
        mto_orders = db.query(FactProduction.order_number, FactProduction.sales_order, FactProduction.release_date)\
            .filter(FactProduction.is_mto == True)\
            .filter(FactProduction.sales_order.isnot(None))\
            .limit(20).all()
            
        print(f"Found {len(mto_orders)} sample MTO orders with SO numbers.")
        
        so_list = [o.sales_order for o in mto_orders if o.sales_order]
        print(f"Sample SO Numbers: {so_list[:5]}")
        
        # 2. Check if these SOs have dates in FactBilling
        so_dates = db.query(FactBilling.so_number, FactBilling.so_date)\
            .filter(FactBilling.so_number.in_(so_list))\
            .group_by(FactBilling.so_number, FactBilling.so_date)\
            .all()
            
        print(f"Found {len(so_dates)} matching Sales Order Dates in FactBilling.")
        
        # 3. Calculate Potential Prep Time
        so_map = {s: d for s, d in so_dates}
        
        print("\n--- Potential Preparation Times ---")
        for order_num, so_num, release_date in mto_orders:
            if so_num in so_map and so_map[so_num] and release_date:
                so_date = so_map[so_num]
                prep_days = (release_date - so_date).days
                print(f"Order {order_num} (SO {so_num}): SO Date={so_date} -> Release={release_date} | Prep = {prep_days} days")
            else:
                 print(f"Order {order_num} (SO {so_num}): SO Date Not Found or Missing Release Date")

    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze_prep_time()
