from src.db.connection import SessionLocal
from src.db.models import FactProduction
import json

def debug_production_record():
    db = SessionLocal()
    
    try:
        prod = db.query(FactProduction).filter(FactProduction.batch == "25L2460910").first()
        
        result = {}
        if prod:
            result = {
                "found": True,
                "batch": prod.batch,
                "order_number": prod.order_number,
                "sales_order": str(prod.sales_order) if prod.sales_order else None,
                "mrp_controller": prod.mrp_controller,
                "is_mto": prod.is_mto,
                "release_date": str(prod.release_date) if prod.release_date else None,
                "actual_finish_date": str(prod.actual_finish_date) if prod.actual_finish_date else None,
                "has_finish_date": prod.actual_finish_date is not None,
                "should_be_processed": prod.actual_finish_date is not None
            }
        else:
            result = {"found": False}
            
        with open("debug_output.json", "w") as f:
            json.dump(result, f, indent=2)
            
        print(json.dumps(result, indent=2))
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_production_record()
