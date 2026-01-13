"""
Create Analytics SQL Views

Views provide pre-aggregated data for dashboards.
Follows CLAUDE.md: Keep SQL readable, no complex CTEs.
"""
from sqlalchemy import text
from src.db.connection import engine


# All view definitions
VIEWS = {
    # View 1: Current inventory snapshot
    "view_inventory_current": """
        CREATE OR REPLACE VIEW view_inventory_current AS
        SELECT 
            fi.plant_code,
            fi.material_code,
            MAX(fi.material_description) as material_description,
            SUM(fi.qty) as current_qty,
            SUM(COALESCE(fi.qty_kg, 0)) as current_qty_kg,
            MAX(fi.uom) as uom,
            MAX(fi.posting_date) as last_movement
        FROM fact_inventory fi
        GROUP BY fi.plant_code, fi.material_code
        HAVING SUM(fi.qty) > 0
        ORDER BY fi.plant_code, fi.material_code
    """,
    
    # View 2: MTO orders with delivery status
    "view_mto_orders": """
        CREATE OR REPLACE VIEW view_mto_orders AS
        SELECT 
            fp.plant_code,
            fp.sales_order,
            fp.order_number,
            fp.material_code,
            fp.material_description,
            fp.order_qty,
            fp.delivered_qty,
            fp.uom,
            CASE 
                WHEN fp.delivered_qty >= fp.order_qty THEN 'COMPLETE'
                WHEN fp.delivered_qty > 0 THEN 'PARTIAL'
                ELSE 'PENDING'
            END as status,
            fp.release_date,
            fp.actual_finish_date
        FROM fact_production fp
        WHERE fp.is_mto = TRUE
        ORDER BY fp.release_date DESC
    """,
    
    # View 3: Production yield dashboard (REMOVED - legacy genealogy decommissioned 2026-01-12)
    # "view_yield_dashboard": """...""",
    
    # View 4: Sales performance vs targets
    "view_sales_performance": """
        CREATE OR REPLACE VIEW view_sales_performance AS
        SELECT 
            fb.salesman_name,
            ft.semester,
            ft.year,
            COUNT(DISTINCT fb.billing_document) as total_invoices,
            SUM(fb.billing_qty) as total_qty,
            fb.uom,
            SUM(fb.net_value) as total_revenue,
            ft.target as semester_target,
            CASE 
                WHEN ft.target > 0 
                THEN ROUND((SUM(fb.net_value) / ft.target * 100)::numeric, 1)
                ELSE 0 
            END as achievement_pct
        FROM fact_billing fb
        LEFT JOIN fact_target ft 
            ON fb.salesman_name = ft.salesman_name
            AND EXTRACT(YEAR FROM fb.billing_date) = ft.year
            AND CASE 
                WHEN EXTRACT(MONTH FROM fb.billing_date) <= 6 THEN 1 
                ELSE 2 
            END = ft.semester
        WHERE fb.salesman_name IS NOT NULL
        GROUP BY fb.salesman_name, ft.semester, ft.year, fb.uom, ft.target
        ORDER BY total_revenue DESC
    """,
    
    # View 5: Active alerts summary
    "view_active_alerts": """
        CREATE OR REPLACE VIEW view_active_alerts AS
        SELECT 
            a.id,
            a.alert_type,
            a.severity,
            a.title,
            a.description,
            a.status,
            a.plant_code,
            a.material_code,
            a.sales_order,
            a.stuck_hours,
            a.yield_pct,
            a.detected_at,
            a.acknowledged_at,
            a.resolved_at
        FROM fact_alert a
        WHERE a.status IN ('ACTIVE', 'ACKNOWLEDGED')
        ORDER BY 
            CASE a.severity 
                WHEN 'CRITICAL' THEN 1 
                WHEN 'WARNING' THEN 2 
                ELSE 3 
            END,
            a.detected_at DESC
    """,
    
    # View 6: Executive KPIs (Updated 2026-01-12: removed legacy yield reference)
    "view_executive_kpis": """
        CREATE OR REPLACE VIEW view_executive_kpis AS
        SELECT 
            (SELECT COALESCE(SUM(net_value), 0) FROM fact_billing) as total_revenue,
            (SELECT COUNT(*) FROM fact_production WHERE is_mto = TRUE) as total_mto_orders,
            (SELECT COUNT(*) FROM fact_production WHERE is_mto = FALSE) as total_mts_orders,
            0::numeric as avg_yield_pct,
            (SELECT COUNT(*) FROM fact_alert WHERE status = 'ACTIVE') as active_alerts,
            (SELECT COUNT(*) FROM fact_inventory) as total_inventory_movements,
            (SELECT COUNT(*) FROM fact_purchase_order) as total_purchase_orders
    """,
    
    # View 7: AR Collection Summary by Division
    "view_ar_collection_summary": """
        CREATE OR REPLACE VIEW view_ar_collection_summary AS
        SELECT 
            CASE dist_channel
                WHEN '11' THEN 'Industry'
                WHEN '13' THEN 'Retails'
                WHEN '15' THEN 'Project'
                ELSE 'Other'
            END as division,
            dist_channel,
            SUM(COALESCE(total_target, 0)) as total_target,
            SUM(COALESCE(total_realization, 0)) as total_realization,
            CASE 
                WHEN SUM(COALESCE(total_target, 0)) > 0 
                THEN ROUND((SUM(COALESCE(total_realization, 0)) / SUM(total_target) * 100)::numeric, 0)
                ELSE 0 
            END as collection_rate_pct,
            MAX(report_date) as report_date
        FROM fact_ar_aging
        GROUP BY dist_channel
        ORDER BY 
            CASE dist_channel
                WHEN '11' THEN 1
                WHEN '13' THEN 2
                WHEN '15' THEN 3
                ELSE 4
            END
    """,
    
    # View 8: AR Aging Detail
    "view_ar_aging_detail": """
        CREATE OR REPLACE VIEW view_ar_aging_detail AS
        SELECT 
            CASE dist_channel
                WHEN '11' THEN 'Industry'
                WHEN '13' THEN 'Retails'
                WHEN '15' THEN 'Project'
                ELSE 'Other'
            END as division,
            salesman_name,
            customer_name,
            total_target,
            total_realization,
            CASE 
                WHEN total_target > 0 
                THEN ROUND((total_realization / total_target * 100)::numeric, 0)
                ELSE 0 
            END as collection_rate_pct,
            COALESCE(realization_not_due, 0) as not_due,
            COALESCE(target_1_30, 0) as target_1_30,
            COALESCE(target_31_60, 0) as target_31_60,
            COALESCE(target_61_90, 0) as target_61_90,
            COALESCE(target_91_120, 0) as target_91_120,
            COALESCE(target_121_180, 0) as target_121_180,
            COALESCE(target_over_180, 0) as target_over_180,
            CASE 
                WHEN COALESCE(target_over_180, 0) > 0 THEN 'HIGH'
                WHEN COALESCE(target_91_120, 0) + COALESCE(target_121_180, 0) > 0 THEN 'MEDIUM'
                ELSE 'LOW'
            END as risk_level,
            report_date
        FROM fact_ar_aging
        WHERE total_target > 0 OR total_realization > 0
    """
}


def create_all_views():
    """Create all analytics views"""
    print("\n🔧 Creating analytics views...")
    success_count = 0
    error_count = 0
    
    for view_name, view_sql in VIEWS.items():
        # Use separate connection for each view to avoid transaction errors
        try:
            with engine.begin() as conn:
                conn.execute(text(view_sql))
                print(f"  ✓ {view_name}")
                success_count += 1
        except Exception as e:
            print(f"  ✗ {view_name}: {str(e)[:100]}")
            error_count += 1
    
    print(f"\n✓ Created {success_count} views ({error_count} errors)\n")


def drop_all_views():
    """Drop all analytics views"""
    print("\n🗑️  Dropping analytics views...")
    with engine.begin() as conn:
        for view_name in VIEWS.keys():
            try:
                conn.execute(text(f"DROP VIEW IF EXISTS {view_name} CASCADE"))
                print(f"  ✓ Dropped {view_name}")
            except Exception as e:
                print(f"  ✗ {view_name}: {e}")
    print("✓ All views dropped\n")


if __name__ == '__main__':
    create_all_views()
