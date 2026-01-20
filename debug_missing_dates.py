#!/usr/bin/env python3
"""Debug missing delivery_date issue - ClaudeKit compliant investigation"""
from src.db.connection import SessionLocal
from src.db.models import FactDelivery, RawZrsd004

db = SessionLocal()

deliveries = ['1910053734', '1910053733', '1910053732', '1960001173']

print('=' * 70)
print('DEBUG: Missing Delivery Date Investigation')
print('=' * 70)

for d in deliveries:
    fact_records = db.query(FactDelivery).filter(FactDelivery.delivery == d).all()
    raw_records = db.query(RawZrsd004).filter(RawZrsd004.delivery == d).all()
    
    print(f'\n📦 Delivery: {d}')
    print(f'  Fact table: {len(fact_records)} records')
    for f in fact_records[:3]:
        print(f'    Line {f.line_item}: delivery_date={f.delivery_date}, actual={f.actual_gi_date}')
    
    print(f'  Raw table: {len(raw_records)} records')
    for r in raw_records[:3]:
        print(f'    Line {r.line_item}: delivery_date={r.delivery_date}, actual={r.actual_gi_date}')

db.close()
print('\n' + '=' * 70)
