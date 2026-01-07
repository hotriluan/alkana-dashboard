from src.db.connection import SessionLocal
from src.db.models import FactLeadTime

db = SessionLocal()

try:
    # Check order_type distribution with channel
    print("=== ORDER TYPE DISTRIBUTION (WITH CHANNEL) ===")
    
    # Total with channel
    total_with_channel = db.query(FactLeadTime).filter(FactLeadTime.channel_code.isnot(None)).count()
    print(f"Total with channel: {total_with_channel}")
    
    # By order type
    from sqlalchemy import func
    results = db.query(
        FactLeadTime.order_type,
        FactLeadTime.channel_code,
        func.count(FactLeadTime.id).label('count')
    )\
    .filter(FactLeadTime.channel_code.isnot(None))\
    .group_by(FactLeadTime.order_type, FactLeadTime.channel_code)\
    .all()
    
    print("\nBreakdown by Order Type and Channel:")
    for row in results:
        print(f"  {row.order_type} - Channel {row.channel_code}: {row.count} orders")
        
    # Check if MTS has any channel
    mts_with_channel = db.query(FactLeadTime)\
        .filter(FactLeadTime.order_type == 'MTS')\
        .filter(FactLeadTime.channel_code.isnot(None))\
        .count()
    
    print(f"\nMTS orders with channel: {mts_with_channel}")
    
    # Sample MTS order
    mts_sample = db.query(FactLeadTime)\
        .filter(FactLeadTime.order_type == 'MTS')\
        .first()
    
    if mts_sample:
        print(f"\nSample MTS Order:")
        print(f"  Order: {mts_sample.order_number}")
        print(f"  Batch: {mts_sample.batch}")
        print(f"  Channel: {mts_sample.channel_code}")
        
finally:
    db.close()
