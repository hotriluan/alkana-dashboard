#!/usr/bin/env python3
"""
Debug script: Kiểm tra dữ liệu ZRFI005 và AR aging
"""
from datetime import date
from src.db.connection import SessionLocal
from src.db.models import RawZrfi005, FactArAging

def debug_ar_data():
    db = SessionLocal()
    
    target_date = date(2026, 1, 7)
    
    print("\n" + "="*80)
    print("🔍 DEBUG: AR ZRFI005 Data Analysis")
    print("="*80)
    
    # 1. Kiểm tra raw_zrfi005
    print(f"\n1️⃣  RAW_ZRFI005 (snapshot: {target_date})")
    print("-" * 80)
    
    raw_records = db.query(RawZrfi005).filter(
        RawZrfi005.snapshot_date == target_date
    ).all()
    
    print(f"   Total records: {len(raw_records)}")
    
    if raw_records:
        # Aggregate từ raw data
        total_target = sum(r.total_target or 0 for r in raw_records)
        total_realization = sum(r.total_realization or 0 for r in raw_records)
        
        print(f"   Total Target: {total_target:,.0f}")
        print(f"   Total Realization: {total_realization:,.0f}")
        print(f"   Collection Rate: {(total_realization/total_target*100 if total_target else 0):.1f}%")
        
        # Show distinct customers
        customers = set(r.customer_name for r in raw_records if r.customer_name)
        print(f"   Distinct Customers: {len(customers)}")
        
        # Show first 5 records
        print("\n   📄 Sample records:")
        for i, r in enumerate(raw_records[:5]):
            print(f"      {i+1}. {r.customer_name} | Ch: {r.dist_channel} | Gr: {r.cust_group} | Salesm: {r.salesman_name}")
            print(f"         Target: {r.total_target:,.0f} | Real: {r.total_realization:,.0f}")
    else:
        print("   ⚠️  NO RECORDS FOUND")
    
    # 2. Kiểm tra fact_ar_aging
    print(f"\n2️⃣  FACT_AR_AGING (snapshot: {target_date})")
    print("-" * 80)
    
    fact_records = db.query(FactArAging).filter(
        FactArAging.snapshot_date == target_date
    ).all()
    
    print(f"   Total records: {len(fact_records)}")
    
    if fact_records:
        # Aggregate từ fact data
        total_target = sum(r.total_target or 0 for r in fact_records)
        total_realization = sum(r.total_realization or 0 for r in fact_records)
        
        print(f"   Total Target: {total_target:,.0f}")
        print(f"   Total Realization: {total_realization:,.0f}")
        print(f"   Collection Rate: {(total_realization/total_target*100 if total_target else 0):.1f}%")
        
        # Show first 5 records
        print("\n   📄 Sample records:")
        for i, r in enumerate(fact_records[:5]):
            print(f"      {i+1}. {r.customer_name} | Ch: {r.dist_channel}")
            print(f"         Target: {r.total_target:,.0f} | Real: {r.total_realization:,.0f}")
    else:
        print("   ⚠️  NO RECORDS FOUND")
    
    # 3. Kiểm tra discrepancy
    print(f"\n3️⃣  COMPARISON")
    print("-" * 80)
    
    raw_count = len(raw_records)
    fact_count = len(fact_records)
    
    if raw_count > 0 and fact_count > 0:
        raw_total_target = sum(r.total_target or 0 for r in raw_records)
        fact_total_target = sum(r.total_target or 0 for r in fact_records)
        
        print(f"   Raw records:  {raw_count}")
        print(f"   Fact records: {fact_count}")
        print(f"   Difference:   {raw_count - fact_count} records")
        
        if raw_total_target != fact_total_target:
            print(f"\n   ⚠️  DATA MISMATCH!")
            print(f"   Raw Total Target:  {raw_total_target:,.0f}")
            print(f"   Fact Total Target: {fact_total_target:,.0f}")
            print(f"   Difference:        {raw_total_target - fact_total_target:,.0f}")
    
    # 4. Kiểm tra record chi tiết
    print(f"\n4️⃣  MISSING IN FACT TABLE")
    print("-" * 80)
    
    if raw_records and fact_records:
        raw_customers = {(r.customer_name, r.dist_channel, r.cust_group, r.salesman_name) 
                        for r in raw_records}
        fact_customers = {(r.customer_name, r.dist_channel, r.cust_group, r.salesman_name) 
                         for r in fact_records}
        
        missing = raw_customers - fact_customers
        
        if missing:
            print(f"   Found {len(missing)} missing records in fact table:")
            for i, (cust, ch, gr, sales) in enumerate(list(missing)[:5]):
                print(f"      {i+1}. {cust} | Ch: {ch} | Gr: {gr} | Salesm: {sales}")
            if len(missing) > 5:
                print(f"      ... and {len(missing)-5} more")
        else:
            print("   ✓ All raw records exist in fact table")
    
    print("\n" + "="*80 + "\n")
    
    db.close()

if __name__ == '__main__':
    debug_ar_data()
