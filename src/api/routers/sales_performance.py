"""
Sales Performance Dashboard API Router

Tracks sales metrics, trends, and customer performance.
Query directly from fact_billing for proper date filtering.
Follows CLAUDE.md: KISS, DRY, file <200 lines.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from src.api.deps import get_db, get_current_user


router = APIRouter(prefix="/sales", tags=["Sales Performance"])


# ========== Pydantic Models ==========

class SalesRecord(BaseModel):
    """Sales performance record"""
    customer_name: str
    division_code: str
    sales_amount: float
    sales_qty: float
    order_count: int
    avg_order_value: float


class SalesKPIs(BaseModel):
    """Sales dashboard KPIs"""
    total_sales: float
    total_customers: int
    avg_order_value: float
    total_orders: int


class MonthlySalesData(BaseModel):
    """Monthly sales trend data"""
    month_num: int
    month_name: str
    revenue: float
    orders: int


# ========== Helper ==========

def build_date_filter(start_date: Optional[str], end_date: Optional[str]) -> tuple[str, dict]:
    """Build date filter SQL and params"""
    if start_date and end_date:
        return "WHERE billing_date BETWEEN :start_date AND :end_date", {
            "start_date": start_date,
            "end_date": end_date
        }
    return "", {}


# ========== Endpoints ==========

@router.get("/summary", response_model=SalesKPIs)
async def get_sales_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get sales performance summary KPIs with date filtering"""
    where_sql, params = build_date_filter(start_date, end_date)
    
    query = f"""
        SELECT 
            COALESCE(SUM(net_value), 0) as total_sales,
            COUNT(DISTINCT customer_name) as total_customers,
            COALESCE(AVG(net_value), 0) as avg_order,
            COUNT(DISTINCT billing_document) as total_orders
        FROM fact_billing
        {where_sql}
    """
    
    result = db.execute(text(query), params).fetchone()
    
    return SalesKPIs(
        total_sales=float(result[0] or 0),
        total_customers=int(result[1] or 0),
        avg_order_value=round(float(result[2] or 0), 2),
        total_orders=int(result[3] or 0)
    )


@router.get("/customers", response_model=list[SalesRecord])
async def get_sales_by_customer(
    division_code: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get sales by customer with optional division and date filters"""
    where_clauses = []
    params = {"limit": limit}
    
    if division_code:
        where_clauses.append("dist_channel = :division_code")
        params["division_code"] = division_code
    
    if start_date and end_date:
        where_clauses.append("billing_date BETWEEN :start_date AND :end_date")
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    results = db.execute(text(f"""
        SELECT 
            customer_name,
            COALESCE(dist_channel, '') as division_code,
            SUM(net_value) as sales_amount,
            SUM(billing_qty) as sales_qty,
            COUNT(DISTINCT billing_document) as order_count,
            AVG(net_value) as avg_order_value
        FROM fact_billing
        {where_sql}
        GROUP BY customer_name, dist_channel
        ORDER BY sales_amount DESC
        LIMIT :limit
    """), params).fetchall()
    
    return [SalesRecord(
        customer_name=str(r[0]) if r[0] else '',
        division_code=str(r[1]) if r[1] else '',
        sales_amount=float(r[2] or 0),
        sales_qty=float(r[3] or 0),
        order_count=int(r[4] or 0),
        avg_order_value=float(r[5] or 0)
    ) for r in results]


@router.get("/by-division", response_model=list[dict])
async def get_sales_by_division(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get sales aggregated by division with date filtering"""
    where_sql, params = build_date_filter(start_date, end_date)
    
    results = db.execute(text(f"""
        SELECT 
            COALESCE(dist_channel, 'Unknown') as division_code,
            COUNT(DISTINCT customer_name) as customer_count,
            SUM(net_value) as total_sales,
            COUNT(DISTINCT billing_document) as total_orders,
            AVG(net_value) as avg_order_value
        FROM fact_billing
        {where_sql}
        GROUP BY dist_channel
        ORDER BY total_sales DESC
    """), params).fetchall()
    
    return [
        {
            "division_code": str(r[0]),
            "customer_count": int(r[1] or 0),
            "total_sales": float(r[2] or 0),
            "total_orders": int(r[3] or 0),
            "avg_order_value": round(float(r[4] or 0), 2)
        }
        for r in results
    ]


@router.get("/top-customers", response_model=list[SalesRecord])
async def get_top_customers(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get top customers by sales amount with date filtering"""
    where_sql, params = build_date_filter(start_date, end_date)
    params["limit"] = limit
    
    # Append to WHERE or create new
    if where_sql:
        where_sql = where_sql.replace("WHERE", "WHERE net_value > 0 AND")
    else:
        where_sql = "WHERE net_value > 0"
    
    results = db.execute(text(f"""
        SELECT 
            customer_name,
            COALESCE(dist_channel, '') as division_code,
            SUM(net_value) as sales_amount,
            SUM(billing_qty) as sales_qty,
            COUNT(DISTINCT billing_document) as order_count,
            AVG(net_value) as avg_order_value
        FROM fact_billing
        {where_sql}
        GROUP BY customer_name, dist_channel
        ORDER BY sales_amount DESC
        LIMIT :limit
    """), params).fetchall()
    
    return [SalesRecord(
        customer_name=str(r[0]) if r[0] else '',
        division_code=str(r[1]) if r[1] else '',
        sales_amount=float(r[2] or 0),
        sales_qty=float(r[3] or 0),
        order_count=int(r[4] or 0),
        avg_order_value=float(r[5] or 0)
    ) for r in results]


@router.get("/trend", response_model=list[MonthlySalesData])
async def get_monthly_sales_trend(
    year: int = Query(2026, ge=2024, le=2030, description="Year for trend analysis"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get monthly sales trend for specified year"""
    params = {"year": year}
    
    results = db.execute(text("""
        SELECT 
            EXTRACT(MONTH FROM billing_date)::int as month_num,
            TRIM(TO_CHAR(billing_date, 'Month')) as month_name,
            SUM(net_value) as total_revenue,
            COUNT(DISTINCT billing_document) as order_count
        FROM fact_billing
        WHERE EXTRACT(YEAR FROM billing_date) = :year
        GROUP BY EXTRACT(MONTH FROM billing_date), TO_CHAR(billing_date, 'Month')
        ORDER BY month_num ASC
    """), params).fetchall()
    
    # Handle empty results gracefully
    if not results:
        return []
    
    return [MonthlySalesData(
        month_num=int(r[0]),
        month_name=r[1],
        revenue=float(r[2] or 0),
        orders=int(r[3] or 0)
    ) for r in results]


# ========== NEW VISUAL INTELLIGENCE ENDPOINTS ==========

@router.get("/segmentation")
async def get_customer_segmentation(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Customer segmentation by order frequency and revenue
    
    Query Params:
        - start_date: Start of analysis period (defaults to first day of current month)
        - end_date: End of analysis period (defaults to today)
    
    Returns: List of customers for scatter plot (VIP vs Casual)
    """
    from src.core.sales_analytics import SalesAnalytics
    from datetime import datetime
    
    analytics = SalesAnalytics(db)
    
    # Parse date strings to date objects
    start = datetime.fromisoformat(start_date).date() if start_date else None
    end = datetime.fromisoformat(end_date).date() if end_date else None
    
    result = analytics.get_customer_segmentation(start_date=start, end_date=end)
    
    return [item.dict() for item in result]


@router.get("/churn-risk")
async def get_churn_risk(
    limit: int = Query(5, ge=1, le=20, description="Number of at-risk customers"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Identify customers at churn risk
    Logic: High revenue last month + zero orders this month
    """
    from src.core.sales_analytics import SalesAnalytics
    
    analytics = SalesAnalytics(db)
    result = analytics.get_churn_risk(limit=limit)
    
    return [item.dict() for item in result]
