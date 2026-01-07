from src.db.connection import engine
from sqlalchemy import text, inspect

print("=== FACT_AR_AGING TABLE SCHEMA ===\n")

# Get table inspector
inspector = inspect(engine)

# Get columns
columns = inspector.get_columns('fact_ar_aging')
print("Columns:")
for col in columns:
    print(f"  - {col['name']}: {col['type']}")

print("\n=== SAMPLE DATA (First 5 rows) ===\n")
result = engine.connect().execute(text("""
    SELECT * FROM fact_ar_aging LIMIT 5
"""))

rows = result.fetchall()
for i, row in enumerate(rows, 1):
    print(f"\nRow {i}:")
    for j, col in enumerate(result.keys()):
        print(f"  {col}: {row[j]}")

print("\n=== COLUMN STATISTICS ===\n")

# Check which columns have non-zero values
result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(CASE WHEN total_target > 0 THEN 1 END) as has_target,
        COUNT(CASE WHEN total_realization > 0 THEN 1 END) as has_realization,
        COUNT(CASE WHEN target_1_30 > 0 THEN 1 END) as has_target_1_30,
        COUNT(CASE WHEN target_31_60 > 0 THEN 1 END) as has_target_31_60,
        COUNT(CASE WHEN target_61_90 > 0 THEN 1 END) as has_target_61_90,
        COUNT(CASE WHEN target_91_120 > 0 THEN 1 END) as has_target_91_120,
        COUNT(CASE WHEN target_121_180 > 0 THEN 1 END) as has_target_121_180,
        COUNT(CASE WHEN target_over_180 > 0 THEN 1 END) as has_target_over_180,
        COUNT(CASE WHEN realization_not_due > 0 THEN 1 END) as has_real_not_due,
        COUNT(CASE WHEN realization_1_30 > 0 THEN 1 END) as has_real_1_30,
        COUNT(CASE WHEN realization_31_60 > 0 THEN 1 END) as has_real_31_60,
        COUNT(CASE WHEN realization_61_90 > 0 THEN 1 END) as has_real_61_90,
        COUNT(CASE WHEN realization_91_120 > 0 THEN 1 END) as has_real_91_120,
        COUNT(CASE WHEN realization_121_180 > 0 THEN 1 END) as has_real_121_180,
        COUNT(CASE WHEN realization_over_180 > 0 THEN 1 END) as has_real_over_180
    FROM fact_ar_aging
""")).fetchone()

print(f"Total Rows: {result[0]}")
print(f"\nTarget columns with values:")
print(f"  total_target: {result[1]} rows")
print(f"  target_1_30: {result[3]} rows")
print(f"  target_31_60: {result[4]} rows")
print(f"  target_61_90: {result[5]} rows")
print(f"  target_91_120: {result[6]} rows")
print(f"  target_121_180: {result[7]} rows")
print(f"  target_over_180: {result[8]} rows")

print(f"\nRealization columns with values:")
print(f"  total_realization: {result[2]} rows")
print(f"  realization_not_due: {result[9]} rows")
print(f"  realization_1_30: {result[10]} rows")
print(f"  realization_31_60: {result[11]} rows")
print(f"  realization_61_90: {result[12]} rows")
print(f"  realization_91_120: {result[13]} rows")
print(f"  realization_121_180: {result[14]} rows")
print(f"  realization_over_180: {result[15]} rows")

print("\n=== TARGET VS REALIZATION TOTALS ===\n")
result = engine.connect().execute(text("""
    SELECT 
        SUM(total_target) as sum_all_target,
        SUM(target_1_30 + target_31_60 + target_61_90 + target_91_120 + target_121_180 + target_over_180) as sum_target_buckets,
        SUM(total_realization) as sum_all_realization,
        SUM(realization_not_due + realization_1_30 + realization_31_60 + realization_61_90 + 
            realization_91_120 + realization_121_180 + realization_over_180) as sum_real_buckets
    FROM fact_ar_aging
""")).fetchone()

print(f"Total Target (from total_target column): {result[0]:,.0f}")
print(f"Sum of Target buckets: {result[1]:,.0f}")
print(f"Total Realization (from total_realization column): {result[2]:,.0f}")
print(f"Sum of Realization buckets: {result[3]:,.0f}")

# Check for overdue definition
print("\n=== WHAT IS 'OVERDUE'? ===\n")
print("Option 1: Overdue Target (未収金 in Target buckets)")
result = engine.connect().execute(text("""
    SELECT 
        SUM(target_31_60 + target_61_90 + target_91_120 + target_121_180 + target_over_180) as overdue_target
    FROM fact_ar_aging
""")).fetchone()
print(f"  Overdue Target (31+ days): {result[0]:,.0f}")

print("\nOption 2: Overdue Realization (実際の延滞)")
result = engine.connect().execute(text("""
    SELECT 
        SUM(realization_1_30 + realization_31_60 + realization_61_90 + 
            realization_91_120 + realization_121_180 + realization_over_180) as overdue_real
    FROM fact_ar_aging
""")).fetchone()
print(f"  Overdue Realization (all overdue buckets): {result[0]:,.0f}")
