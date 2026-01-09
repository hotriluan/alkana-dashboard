"""
Executive Dashboard API Router

Provides high-level KPIs and aggregated metrics across all business areas.
Follows CLAUDE.md: KISS, DRY, file <200 lines.
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from src.api.deps import get_db, get_current_user


router = APIRouter(prefix="/executive", tags=["Executive Dashboard"])


# ========== Pydantic Models ==========

class ExecutiveKPIs(BaseModel):
    """Executive dashboard summary metrics"""
    # Revenue metrics
    total_revenue: float
    revenue_growth_pct: float
    
    # Customer metrics
    total_customers: int
    active_customers: int
    
    # Production metrics
    total_orders: int
    completed_orders: int
    completion_rate: float
    
    # Inventory metrics
    total_inventory_value: float
    inventory_items: int
    
    # AR metrics
    total_ar: float
    overdue_ar: float
    overdue_pct: float


class RevenueByDivision(BaseModel):
    """Revenue breakdown by division"""
    division_code: str
    revenue: float
    customer_count: int
    order_count: int


class TopCustomer(BaseModel):
    """Top customer by revenue"""
    customer_name: str
    revenue: float
    order_count: int


class ProductionTrend(BaseModel):
    """Production trend data"""
    period: str
    orders_created: int
    orders_completed: int
    yield_pct: float


# ========== Endpoints ==========

@router.get("/summary", response_model=ExecutiveKPIs)
async def get_executive_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get executive dashboard summary KPIs"""
    
    # Revenue metrics from fact_billing (with date filter support)
    date_filter = ""
    if start_date and end_date:
        date_filter = f"WHERE billing_date BETWEEN '{start_date}' AND '{end_date}'"
    
    revenue_result = db.execute(text(f"""
        SELECT 
            COALESCE(SUM(net_value), 0) as total_revenue,
            COUNT(DISTINCT customer_name) as total_customers
        FROM fact_billing
        {date_filter}
    """)).fetchone()
    
    # Production metrics
    prod_date_filter = ""
    if start_date and end_date:
        prod_date_filter = f"WHERE actual_finish_date BETWEEN '{start_date}' AND '{end_date}'"
    
    production_result = db.execute(text(f"""
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN system_status LIKE '%%TECO%%' THEN 1 END) as completed_orders,
            COALESCE(AVG(CASE 
                WHEN order_qty > 0 THEN (delivered_qty / order_qty * 100) 
                ELSE 0 
            END), 0) as avg_yield
        FROM fact_production
        {prod_date_filter}
    """)).fetchone()
    
    # Inventory metrics
    inventory_result = db.execute(text("""
        SELECT 
            COUNT(DISTINCT material_code) as inventory_items,
            COALESCE(SUM(current_qty), 0) as total_qty
        FROM view_inventory_current
    """)).fetchone()
    
    # AR metrics - Total AR from latest snapshot only (not sum of all snapshots)
    ar_result = db.execute(text("""
        SELECT 
            COALESCE(SUM(total_target), 0) as total_ar,
            COALESCE(SUM(COALESCE(target_31_60, 0) + COALESCE(target_61_90, 0) + 
                         COALESCE(target_91_120, 0) + COALESCE(target_121_180, 0) + 
                         COALESCE(target_over_180, 0)), 0) as overdue_ar
        FROM fact_ar_aging
        WHERE snapshot_date = (
            SELECT MAX(snapshot_date) 
            FROM fact_ar_aging 
            WHERE snapshot_date IS NOT NULL
        )
    """)).fetchone()
    
    total_orders = int(production_result[0] or 0)
    completed_orders = int(production_result[1] or 0)
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    
    total_ar = float(ar_result[0] or 0)
    overdue_ar = float(ar_result[1] or 0)
    overdue_pct = (overdue_ar / total_ar * 100) if total_ar > 0 else 0
    
    return ExecutiveKPIs(
        total_revenue=float(revenue_result[0] or 0),
        revenue_growth_pct=0.0,  # TODO: Calculate period comparison
        total_customers=int(revenue_result[1] or 0),
        active_customers=int(revenue_result[1] or 0),
        total_orders=total_orders,
        completed_orders=completed_orders,
        completion_rate=round(completion_rate, 2),
        total_inventory_value=0.0,  # TODO: Add valuation
        inventory_items=int(inventory_result[0] or 0),
        total_ar=total_ar,
        overdue_ar=overdue_ar,
        overdue_pct=round(overdue_pct, 2)
    )


@router.get("/revenue-by-division", response_model=list[RevenueByDivision])
async def get_revenue_by_division(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get revenue breakdown by distribution channel"""
    date_filter = ""
    if start_date and end_date:
        date_filter = f"WHERE billing_date BETWEEN '{start_date}' AND '{end_date}'"
    
    result = db.execute(text(f"""
        SELECT 
            COALESCE(dist_channel, 'N/A') as division_code,
            SUM(net_value) as revenue,
            COUNT(DISTINCT COALESCE(customer_name, 'Unknown')) as customer_count,
            COUNT(DISTINCT billing_document) as order_count
        FROM fact_billing
        {date_filter}
        GROUP BY dist_channel
        ORDER BY revenue DESC
        LIMIT {limit}
    """))
    
    return [
        RevenueByDivision(
            division_code=row[0] or "N/A",
            revenue=float(row[1] or 0),
            customer_count=int(row[2] or 0),
            order_count=int(row[3] or 0)
        )
        for row in result
    ]


@router.get("/top-customers", response_model=list[TopCustomer])
async def get_top_customers(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get top customers by revenue"""
    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND billing_date BETWEEN '{start_date}' AND '{end_date}'"
    
    result = db.execute(text(f"""
        SELECT 
            COALESCE(customer_name, 'Unknown') as customer_name,
            SUM(net_value) as revenue,
            COUNT(DISTINCT billing_document) as order_count
        FROM fact_billing
        WHERE customer_name IS NOT NULL {date_filter}
        GROUP BY customer_name
        ORDER BY revenue DESC
        LIMIT {limit}
    """))
    
    return [
        TopCustomer(
            customer_name=row[0],
            revenue=float(row[1] or 0),
            order_count=int(row[2] or 0)
        )
        for row in result
    ]
