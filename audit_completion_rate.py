"""
Audit script for Completion Rate metric
Investigates why 2025 completion rate is 9.54%
"""
import sys
from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = "postgresql://postgres:password123@localhost:5432/alkana_dashboard"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("COMPLETION RATE AUDIT - 2025 Full Year Analysis")
print("=" * 80)

with engine.connect() as conn:
    # Query 1: Count orders by system_status for 2025
    print("\n### QUERY 1: Orders by Status (2025 actual_finish_date filter) ###\n")
    result = conn.execute(text("""
        SELECT 
            system_status,
            COUNT(*) as count
        FROM fact_production
        WHERE actual_finish_date BETWEEN '2025-01-01' AND '2025-12-31'
        GROUP BY system_status
        ORDER BY count DESC
    """))
    
    total_2025 = 0
    status_breakdown = []
    for row in result:
        status_breakdown.append((row[0], row[1]))
        total_2025 += row[1]
        print(f"  {row[0]:<20} : {row[1]:>8,}")
    
    print(f"\n  {'TOTAL':<20} : {total_2025:>8,}")
    
    # Query 2: Current logic - TECO only
    print("\n### QUERY 2: Current Backend Logic (TECO filter) ###\n")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN system_status LIKE '%TECO%' THEN 1 END) as completed_orders
        FROM fact_production
        WHERE actual_finish_date BETWEEN '2025-01-01' AND '2025-12-31'
    """))
    
    row = result.fetchone()
    total = row[0]
    completed = row[1]
    rate = (completed / total * 100) if total > 0 else 0
    
    print(f"  Total Orders:      {total:>8,}")
    print(f"  Completed (TECO):  {completed:>8,}")
    print(f"  Completion Rate:   {rate:>7.2f}%")
    
    # Query 3: Alternative logic - DLV OR TECO
    print("\n### QUERY 3: Proposed Fix (DLV OR TECO) ###\n")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN system_status LIKE '%DLV%' OR system_status LIKE '%TECO%' THEN 1 END) as completed_orders
        FROM fact_production
        WHERE actual_finish_date BETWEEN '2025-01-01' AND '2025-12-31'
    """))
    
    row = result.fetchone()
    total_alt = row[0]
    completed_alt = row[1]
    rate_alt = (completed_alt / total_alt * 100) if total_alt > 0 else 0
    
    print(f"  Total Orders:      {total_alt:>8,}")
    print(f"  Completed (DLV|TECO): {completed_alt:>8,}")
    print(f"  Completion Rate:   {rate_alt:>7.2f}%")
    
    # Query 4: Check DLV vs TECO breakdown
    print("\n### QUERY 4: DLV vs TECO Breakdown ###\n")
    result = conn.execute(text("""
        SELECT 
            COUNT(CASE WHEN system_status LIKE '%DLV%' THEN 1 END) as dlv_only,
            COUNT(CASE WHEN system_status LIKE '%TECO%' THEN 1 END) as teco_only,
            COUNT(CASE WHEN system_status LIKE '%DLV%' AND system_status LIKE '%TECO%' THEN 1 END) as both
        FROM fact_production
        WHERE actual_finish_date BETWEEN '2025-01-01' AND '2025-12-31'
    """))
    
    row = result.fetchone()
    print(f"  Contains 'DLV':    {row[0]:>8,}")
    print(f"  Contains 'TECO':   {row[1]:>8,}")
    print(f"  Contains BOTH:     {row[2]:>8,}")
    
    # Query 5: Zombie orders (Created long ago, still in REL/CRTD)
    print("\n### QUERY 5: Zombie Orders (Created > 6 months ago, not finished) ###\n")
    result = conn.execute(text("""
        SELECT 
            system_status,
            COUNT(*) as count
        FROM fact_production
        WHERE basic_start_date < '2025-07-01'
          AND (actual_finish_date IS NULL OR actual_finish_date > '2025-12-31')
          AND system_status NOT LIKE '%TECO%'
          AND system_status NOT LIKE '%DLV%'
        GROUP BY system_status
        ORDER BY count DESC
        LIMIT 10
    """))
    
    zombie_total = 0
    for row in result:
        zombie_total += row[1]
        print(f"  {row[0]:<20} : {row[1]:>8,}")
    
    print(f"\n  {'TOTAL ZOMBIES':<20} : {zombie_total:>8,}")
    
    # Query 6: Date column analysis
    print("\n### QUERY 6: Date Column Usage Check ###\n")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN basic_start_date IS NOT NULL THEN 1 END) as has_start,
            COUNT(CASE WHEN scheduled_finish IS NOT NULL THEN 1 END) as has_scheduled,
            COUNT(CASE WHEN actual_finish_date IS NOT NULL THEN 1 END) as has_actual
        FROM fact_production
        WHERE actual_finish_date BETWEEN '2025-01-01' AND '2025-12-31'
    """))
    
    row = result.fetchone()
    print(f"  Total orders:        {row[0]:>8,}")
    print(f"  Has basic_start:     {row[1]:>8,} ({row[1]/row[0]*100:.1f}%)")
    print(f"  Has scheduled_finish:{row[2]:>8,} ({row[2]/row[0]*100:.1f}%)")
    print(f"  Has actual_finish:   {row[3]:>8,} ({row[3]/row[0]*100:.1f}%)")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
