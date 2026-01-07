from src.db.connection import engine
from sqlalchemy import text

# Check AR aging data
print("=== Checking AR Aging Data ===\n")

# Check total AR
result = engine.connect().execute(text("""
    SELECT 
        SUM(total_target) as sum_target,
        SUM(total_realization) as sum_realization,
        COUNT(*) as row_count
    FROM fact_ar_aging
""")).fetchone()

print(f"Total Target: {result[0]:,.0f}")
print(f"Total Realization: {result[1]:,.0f}")
print(f"Row Count: {result[2]}")

# Check overdue buckets
print("\n=== Target Buckets ===")
result = engine.connect().execute(text("""
    SELECT 
        SUM(target_1_30) as t_1_30,
        SUM(target_31_60) as t_31_60,
        SUM(target_61_90) as t_61_90,
        SUM(target_91_120) as t_91_120,
        SUM(target_121_180) as t_121_180,
        SUM(target_over_180) as t_over_180
    FROM fact_ar_aging
""")).fetchone()

print(f"1-30 days: {result[0] or 0:,.0f}")
print(f"31-60 days: {result[1] or 0:,.0f}")
print(f"61-90 days: {result[2] or 0:,.0f}")
print(f"91-120 days: {result[3] or 0:,.0f}")
print(f"121-180 days: {result[4] or 0:,.0f}")
print(f"Over 180 days: {result[5] or 0:,.0f}")

print("\n=== Realization Buckets ===")
result = engine.connect().execute(text("""
    SELECT 
        SUM(realization_not_due) as r_not_due,
        SUM(realization_1_30) as r_1_30,
        SUM(realization_31_60) as r_31_60,
        SUM(realization_61_90) as r_61_90,
        SUM(realization_91_120) as r_91_120,
        SUM(realization_121_180) as r_121_180,
        SUM(realization_over_180) as r_over_180
    FROM fact_ar_aging
""")).fetchone()

print(f"Not Due: {result[0] or 0:,.0f}")
print(f"1-30 days: {result[1] or 0:,.0f}")
print(f"31-60 days: {result[2] or 0:,.0f}")
print(f"61-90 days: {result[3] or 0:,.0f}")
print(f"91-120 days: {result[4] or 0:,.0f}")
print(f"121-180 days: {result[5] or 0:,.0f}")
print(f"Over 180 days: {result[6] or 0:,.0f}")

# Calculate overdue
overdue = sum([(result[i] or 0) for i in range(1, 7)])  # Skip not_due (index 0)
total_real = (result[0] or 0) + overdue
print(f"\n=== Calculated Overdue AR ===")
print(f"Overdue AR (sum of all overdue buckets): {overdue:,.0f}")
print(f"Total Realization: {total_real:,.0f}")
