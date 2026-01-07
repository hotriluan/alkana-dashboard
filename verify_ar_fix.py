from src.db.connection import engine
from sqlalchemy import text

print("=== VERIFY OVERDUE CALCULATION ===\n")

# Calculate overdue with COALESCE for NULL handling
result = engine.connect().execute(text("""
    SELECT 
        SUM(total_target) as total_ar,
        SUM(COALESCE(target_31_60, 0) + COALESCE(target_61_90, 0) + 
            COALESCE(target_91_120, 0) + COALESCE(target_121_180, 0) + 
            COALESCE(target_over_180, 0)) as overdue_ar
    FROM fact_ar_aging
""")).fetchone()

total_ar = result[0]
overdue_ar = result[1]
overdue_pct = (overdue_ar / total_ar * 100) if total_ar > 0 else 0

print(f"Total AR: {total_ar:,.0f}")
print(f"Overdue AR: {overdue_ar:,.0f}")
print(f"Overdue %: {overdue_pct:.2f}%")

print("\n=== BREAKDOWN ===")
result = engine.connect().execute(text("""
    SELECT 
        SUM(COALESCE(target_31_60, 0)) as t_31_60,
        SUM(COALESCE(target_61_90, 0)) as t_61_90,
        SUM(COALESCE(target_91_120, 0)) as t_91_120,
        SUM(COALESCE(target_121_180, 0)) as t_121_180,
        SUM(COALESCE(target_over_180, 0)) as t_over_180
    FROM fact_ar_aging
""")).fetchone()

print(f"31-60 days: {result[0]:,.0f}")
print(f"61-90 days: {result[1]:,.0f}")
print(f"91-120 days: {result[2]:,.0f}")
print(f"121-180 days: {result[3]:,.0f}")
print(f"Over 180 days: {result[4]:,.0f}")
print(f"Total Overdue: {sum(result):,.0f}")
