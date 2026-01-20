"""
MTO Orders Dashboard API Router

Provides Make-to-Order production status and delivery tracking.
Follows CLAUDE.md: KISS, DRY, file <200 lines.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from src.api.deps import get_db, get_current_user


router = APIRouter(prefix="/mto-orders", tags=["MTO Orders"])


# ========== Pydantic Models ==========

class MTOOrder(BaseModel):
    """MTO order with delivery status"""
    plant_code: str
    sales_order: str
    order_number: str
    material_code: str
    material_description: str
    order_qty: float
    delivered_qty: float
    uom: str
    status: str
    release_date: Optional[str]
    actual_finish_date: Optional[str]


class MTOKPIs(BaseModel):
    """MTO dashboard KPIs"""
    total_orders: int
    completed_orders: int
    partial_orders: int
    pending_orders: int
    completion_rate: float


# ========== Endpoints ==========

@router.get("/summary", response_model=MTOKPIs)
async def get_mto_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get MTO orders summary KPIs with date filtering"""
    where_sql = ""
    params = {}
    
    if start_date and end_date:
        where_sql = "WHERE release_date BETWEEN :start_date AND :end_date"
        params = {"start_date": start_date, "end_date": end_date}
    
    result = db.execute(text(f"""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'COMPLETE') as completed,
            COUNT(*) FILTER (WHERE status = 'PARTIAL') as partial,
            COUNT(*) FILTER (WHERE status = 'PENDING') as pending
        FROM view_mto_orders
        {where_sql}
    """), params).fetchone()
    
    total = int(result[0] or 0)
    completed = int(result[1] or 0)
    
    return MTOKPIs(
        total_orders=total,
        completed_orders=completed,
        partial_orders=int(result[2] or 0),
        pending_orders=int(result[3] or 0),
        completion_rate=round(completed / total * 100, 1) if total > 0 else 0
    )


@router.get("/orders", response_model=list[MTOOrder])
async def get_mto_orders(
    plant_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get MTO orders with optional filters including date range"""
    where_clauses = []
    params = {"limit": limit}
    
    if plant_code:
        where_clauses.append("plant_code = :plant_code")
        params["plant_code"] = plant_code
    
    if status:
        where_clauses.append("status = :status")
        params["status"] = status.upper()
    
    if start_date and end_date:
        where_clauses.append("release_date BETWEEN :start_date AND :end_date")
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    results = db.execute(text(f"""
        SELECT 
            plant_code, sales_order, order_number, material_code,
            material_description, order_qty, delivered_qty, uom,
            status, release_date::text, actual_finish_date::text
        FROM view_mto_orders
        {where_sql}
        ORDER BY release_date DESC
        LIMIT :limit
    """), params).fetchall()
    
    return [MTOOrder(
        plant_code=str(r[0]) if r[0] else '',
        sales_order=str(r[1]) if r[1] else '',
        order_number=str(r[2]) if r[2] else '',
        material_code=str(r[3]) if r[3] else '',
        material_description=str(r[4]) if r[4] else '',
        order_qty=float(r[5] or 0),
        delivered_qty=float(r[6] or 0),
        uom=str(r[7]) if r[7] else '',
        status=str(r[8]) if r[8] else '',
        release_date=str(r[9]) if r[9] else None,
        actual_finish_date=str(r[10]) if r[10] else None
    ) for r in results]


@router.get("/by-status", response_model=list[dict])
async def get_orders_by_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get order counts grouped by status"""
    results = db.execute(text("""
        SELECT 
            status,
            COUNT(*) as order_count,
            SUM(order_qty) as total_qty
        FROM view_mto_orders
        GROUP BY status
        ORDER BY 
            CASE status 
                WHEN 'PENDING' THEN 1
                WHEN 'PARTIAL' THEN 2
                WHEN 'COMPLETE' THEN 3
                ELSE 4
            END
    """)).fetchall()
    
    return [
        {
            "status": str(r[0]),
            "order_count": int(r[1] or 0),
            "total_qty": float(r[2] or 0)
        }
        for r in results
    ]


# ========== NEW VISUAL INTELLIGENCE ENDPOINTS ==========

@router.get("/funnel")
async def get_production_funnel(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Production order funnel by status
    
    Query Params:
        - start_date: Start of analysis period (defaults to first day of current month)
        - end_date: End of analysis period (defaults to today)
    
    Returns: Stages (Created/Released/In Progress/Completed) with counts
    """
    from src.core.production_analytics import ProductionAnalytics
    from datetime import datetime
    
    analytics = ProductionAnalytics(db)
    
    # Parse date strings to date objects
    start = datetime.fromisoformat(start_date).date() if start_date else None
    end = datetime.fromisoformat(end_date).date() if end_date else None
    
    result = analytics.get_production_funnel(start_date=start, end_date=end)
    
    return [item.dict() for item in result]


@router.get("/top-orders")
async def get_top_orders(
    limit: int = Query(10, ge=5, le=20, description="Number of top orders"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get top orders by quantity for Gantt chart
    Returns: Order details with release/finish dates and delay status
    """
    from src.core.production_analytics import ProductionAnalytics
    
    analytics = ProductionAnalytics(db)
    result = analytics.get_top_orders(limit=limit)
    
    return [item.dict() for item in result]
