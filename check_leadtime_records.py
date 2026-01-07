from src.db.connection import SessionLocal
from src.db.models import FactLeadTime
import json

def check_leadtime_records():
    db = SessionLocal()
    
    try:
        # Get ALL records for this batch
        records = db.query(FactLeadTime).filter(FactLeadTime.batch == "25L2460910").all()
        
        result = {
            "batch": "25L2460910",
            "record_count": len(records),
            "records": []
        }
        
        for rec in records:
            result["records"].append({
                "order_number": rec.order_number,
                "order_type": rec.order_type,
                "prep_days": rec.preparation_days,
                "prod_days": rec.production_days,
                "transit_days": rec.transit_days,
                "storage_days": rec.storage_days,
                "total_days": rec.lead_time_days,
                "start_date": str(rec.start_date) if rec.start_date else None,
                "end_date": str(rec.end_date) if rec.end_date else None
            })
            
        print(json.dumps(result, indent=2))
            
    finally:
        db.close()

if __name__ == "__main__":
    check_leadtime_records()
