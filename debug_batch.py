from src.db.connection import SessionLocal
from src.db.models import FactLeadTime, RawMb51, FactProduction, FactPurchaseOrder
from sqlalchemy import text

def check_batch():
    print("=== CHECKING BATCH 25L2473710 ===")
    db = SessionLocal()
    batch_id = "25L2473710"
    try:
        # Check FactLeadTime
        lead_time = db.query(FactLeadTime).filter(FactLeadTime.batch == batch_id).first()
        if lead_time:
            print(f"[FOUND] FactLeadTime: Order={lead_time.order_number}, Type={lead_time.order_type}, LT={lead_time.lead_time_days}")
        else:
            print("[MISSING] Not found in FactLeadTime")

        # Check RawMb51
        raw_count = db.query(RawMb51).filter(RawMb51.col_6_batch == batch_id).count()
        print(f"RawMb51 Count: {raw_count}")
        
        # Check FactProduction
        prod = db.query(FactProduction).filter(FactProduction.batch == batch_id).first()
        if prod:
            print(f"[FOUND] FactProduction: Order={prod.order_number}, MTO={prod.is_mto}")
            
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_batch()
