"""Create missing database views for new dashboards"""
from sqlalchemy import text
from src.db.connection import engine

def create_views():
    """Create view_yield_dashboard and view_sales_performance"""
    conn = engine.connect()
    
    # Drop existing views
    conn.execute(text("DROP VIEW IF EXISTS view_yield_dashboard CASCADE"))
    conn.execute(text("DROP VIEW IF EXISTS view_sales_performance CASCADE"))
    
    # Create view_yield_dashboard
    conn.execute(text("""
        CREATE VIEW view_yield_dashboard AS
        SELECT 
            fp.plant_code::text,
            fp.material_code::text,
            fp.material_description::text,
            SUM(fp.order_qty) as total_input_qty,
            SUM(fp.delivered_qty) as total_output_qty,
            CASE 
                WHEN SUM(fp.order_qty) > 0 
                THEN ROUND((SUM(fp.delivered_qty) / SUM(fp.order_qty) * 100)::numeric, 1)
                ELSE 0 
            END as yield_percentage,
            SUM(fp.order_qty - fp.delivered_qty) as scrap_qty,
            fp.uom::text
        FROM fact_production fp
        GROUP BY fp.plant_code, fp.material_code, fp.material_description, fp.uom
        HAVING SUM(fp.order_qty) > 0
    """))
    
    # Create view_sales_performance (using real customer data from raw_zrsd002)
    conn.execute(text("""
        CREATE OR REPLACE VIEW view_sales_performance AS
        SELECT 
            r.raw_data->>'Bill-to' as customer_code,
            r.raw_data->>'Name of Bill to' as customer_name,
            r.raw_data->>'Dist Channel' as division_code,
            SUM((r.raw_data->>'Net Value')::numeric) as sales_amount,
            SUM((r.raw_data->>'Billing Qty')::numeric) as sales_qty,
            COUNT(DISTINCT r.raw_data->>'Billing Document') as order_count,
            CASE 
                WHEN COUNT(DISTINCT r.raw_data->>'Billing Document') > 0 
                THEN ROUND((SUM((r.raw_data->>'Net Value')::numeric) / COUNT(DISTINCT r.raw_data->>'Billing Document'))::numeric, 2)
                ELSE 0 
            END as avg_order_value
        FROM raw_zrsd002 r
        WHERE r.raw_data->>'Name of Bill to' IS NOT NULL
          AND r.raw_data->>'Net Value' IS NOT NULL
        GROUP BY 
            r.raw_data->>'Bill-to',
            r.raw_data->>'Name of Bill to',
            r.raw_data->>'Dist Channel'
        HAVING SUM((r.raw_data->>'Net Value')::numeric) > 0
    """))
    
    conn.commit()
    conn.close()
    print("✅ Views created: view_yield_dashboard, view_sales_performance")

if __name__ == "__main__":
    create_views()
