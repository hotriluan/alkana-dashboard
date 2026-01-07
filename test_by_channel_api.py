from src.db.connection import SessionLocal
from src.api.routers.lead_time import get_by_channel
import json

db = SessionLocal()

try:
    result = get_by_channel(db)
    print("=== API /by-channel RESPONSE ===")
    print(json.dumps(result, indent=2, default=str))
finally:
    db.close()
