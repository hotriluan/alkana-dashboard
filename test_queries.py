from src.db.connection import engine
from sqlalchemy import text

# Test production query
print("Testing production query...")
production_result = engine.connect().execute(text("""
    SELECT 
        COUNT(*) as total_orders,
        COUNT(CASE WHEN system_status LIKE '%%TECO%%' THEN 1 END) as completed_orders
    FROM fact_production
""")).fetchone()
print(f"Production: Total={production_result[0]}, Completed={production_result[1]}")

# Test inventory query
print("\nTesting inventory query...")
inventory_result = engine.connect().execute(text("""
    SELECT 
        COUNT(DISTINCT material_code) as inventory_items,
        COALESCE(SUM(quantity_on_hand), 0) as total_qty
    FROM view_inventory_current
""")).fetchone()
print(f"Inventory: Items={inventory_result[0]}, Qty={inventory_result[1]}")

# Test AR query
print("\nTesting AR query...")
ar_result = engine.connect().execute(text("""
    SELECT 
        COALESCE(SUM(total_ar), 0) as total_ar,
        COALESCE(SUM(overdue_ar), 0) as overdue_ar
    FROM fact_ar_aging
""")).fetchone()
print(f"AR: Total={ar_result[0]}, Overdue={ar_result[1]}")
