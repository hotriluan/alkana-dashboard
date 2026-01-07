from src.db.connection import SessionLocal
from src.db.models import FactLeadTime, FactProduction, RawZrsd006, FactBilling
import pandas as pd

db = SessionLocal()

try:
    print("=== TESTING CHANNEL MAPPING LOGIC ===\n")
    
    # 1. Build Material -> Channel map from zrsd006
    import json
    zrsd006_records = db.query(RawZrsd006.raw_data).all()
    
    material_channel_map = {}
    for record in zrsd006_records:
        if record.raw_data:
            data = json.loads(record.raw_data) if isinstance(record.raw_data, str) else record.raw_data
            mat = data.get('Material Code')
            ch = data.get('Distribution Channel')
            
            if mat and ch:
                mat_str = str(mat).strip()
                ch_str = str(ch).strip()
                if mat_str and ch_str:
                    material_channel_map[mat_str] = ch_str
                
    print(f"Material-Channel Map: {len(material_channel_map)} materials")
    print(f"Sample: {list(material_channel_map.items())[:5]}\n")
    
    # 2. Test with random MTS orders
    mts_samples = db.query(FactProduction)\
        .filter(FactProduction.is_mto == False)\
        .filter(FactProduction.actual_finish_date.isnot(None))\
        .limit(10).all()
    
    print("=== TESTING MTS ORDERS ===")
    matched = 0
    for prod in mts_samples:
        material = str(prod.material_code).strip() if prod.material_code else None
        channel = material_channel_map.get(material) if material else None
        
        if channel:
            matched += 1
            print(f"✓ Material {material} → Channel {channel}")
        else:
            print(f"✗ Material {material} → NO MATCH")
            
    print(f"\nMatch Rate: {matched}/{len(mts_samples)} ({matched*100//len(mts_samples)}%)")
    
    # 3. Test with random MTO orders
    print("\n=== TESTING MTO ORDERS ===")
    mto_samples = db.query(FactProduction)\
        .filter(FactProduction.is_mto == True)\
        .filter(FactProduction.actual_finish_date.isnot(None))\
        .limit(10).all()
    
    for prod in mto_samples:
        material = str(prod.material_code).strip() if prod.material_code else None
        channel = material_channel_map.get(material) if material else None
        
        if channel:
            print(f"✓ Material {material} → Channel {channel}")
        else:
            print(f"✗ Material {material} → NO MATCH")
            
finally:
    db.close()
