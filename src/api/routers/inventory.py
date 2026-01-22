"""
Inventory Dashboard API Router

Provides inventory flow analytics based on MB51 movements (fact_inventory).
Calculates throughput, net change, and activity metrics instead of stock balances.
Follows CLAUDE.md: KISS, DRY, file <200 lines.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from src.api.deps import get_db, get_current_user


router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ========== Pydantic Models ==========

class InventoryItem(BaseModel):
    """Current inventory snapshot"""
    plant_code: str
    material_code: str
    material_description: str
    current_qty: float
    current_qty_kg: float
    uom: str
    last_movement: str


class InventoryKPI(BaseModel):
    """Inventory KPIs"""
    total_items: int
    total_materials: int
    total_plants: int
    total_qty_kg: float


class FlowTrend(BaseModel):
    """Weekly flow trend data"""
    period: str
    inbound: float
    outbound: float


# ========== Endpoints ==========

@router.get("/flow-trends", response_model=list[FlowTrend])
async def get_flow_trends(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get weekly inbound vs outbound flow trends from MB51 movements.
    
    Movement Type Classification:
    - Inbound: 101 (GR Purchase), 501 (Transfer Receipt), 561 (Initial Entry)
    - Outbound: 601 (GI Sales), 261 (Production Issue), 551 (Transfer Issue), 351 (Plant to Plant)
    """
    where_sql = ""
    params = {}
    
    if start_date and end_date:
        where_sql = "WHERE posting_date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    results = db.execute(text(f"""
        SELECT 
            TO_CHAR(DATE_TRUNC('week', posting_date), 'YYYY-MM-DD') as period,
            COALESCE(SUM(
                CASE 
                    WHEN mvt_type IN (101, 501, 561) THEN ABS(qty_kg)
                    ELSE 0 
                END
            ), 0) as inbound,
            COALESCE(SUM(
                CASE 
                    WHEN mvt_type IN (601, 261, 551, 351) THEN ABS(qty_kg)
                    ELSE 0 
                END
            ), 0) as outbound
        FROM fact_inventory
        {where_sql}
        GROUP BY DATE_TRUNC('week', posting_date)
        ORDER BY period
    """), params).fetchall()
    
    return [
        FlowTrend(
            period=f"Week {idx+1}" if idx < 10 else str(r[0]),
            inbound=float(r[1] or 0),
            outbound=float(r[2] or 0)
        )
        for idx, r in enumerate(results)
    ]


@router.get("/summary", response_model=InventoryKPI)
async def get_inventory_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get inventory flow summary KPIs from fact_inventory (MB51 movements)"""
    where_sql = ""
    params = {}
    
    if start_date and end_date:
        where_sql = "WHERE posting_date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    result = db.execute(text(f"""
        SELECT 
            COUNT(*) as total_items,
            COUNT(DISTINCT material_code) as total_materials,
            COUNT(DISTINCT plant_code) as total_plants,
            COALESCE(SUM(ABS(qty_kg)), 0) as total_qty_kg
        FROM fact_inventory
        {where_sql}
    """), params).fetchone()
    
    return InventoryKPI(
        total_items=int(result[0] or 0),
        total_materials=int(result[1] or 0),
        total_plants=int(result[2] or 0),
        total_qty_kg=float(result[3] or 0)
    )


@router.get("/items", response_model=list[InventoryItem])
async def get_inventory_items(
    plant_code: Optional[str] = Query(None),
    material_code: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get inventory items with net change and transaction count from fact_inventory"""
    where_clauses = []
    params = {"limit": limit}
    
    if start_date and end_date:
        where_clauses.append("posting_date BETWEEN :start_date AND :end_date")
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    if plant_code:
        where_clauses.append("plant_code = :plant_code")
        params["plant_code"] = plant_code
    
    if material_code:
        where_clauses.append("material_code ILIKE '%' || :material_code || '%'")
        params["material_code"] = material_code
    
    where_sql = "WHERE " + " AND " .join(where_clauses) if where_clauses else ""
    
    results = db.execute(text(f"""
        SELECT 
            plant_code::text,
            material_code,
            material_description,
            COUNT(*) as current_qty,
            SUM(qty_kg) as current_qty_kg,
            MAX(uom) as uom,
            MAX(posting_date)::text as last_movement
        FROM fact_inventory
        {where_sql}
        GROUP BY plant_code, material_code, material_description
        ORDER BY ABS(SUM(qty_kg)) DESC
        LIMIT :limit
    """), params).fetchall()
    
    return [InventoryItem(
        plant_code=str(r[0]) if r[0] else '',
        material_code=str(r[1]) if r[1] else '',
        material_description=str(r[2]) if r[2] else '',
        current_qty=float(r[3] or 0),
        current_qty_kg=float(r[4] or 0),
        uom=str(r[5]) if r[5] else '',
        last_movement=str(r[6]) if r[6] else ''
    ) for r in results]


@router.get("/by-plant", response_model=list[dict])
async def get_inventory_by_plant(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get activity intensity by plant from fact_inventory (transaction count and throughput)"""
    where_sql = ""
    params = {}
    
    if start_date and end_date:
        where_sql = "WHERE posting_date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    results = db.execute(text(f"""
        SELECT 
            plant_code::text,
            COUNT(*) as item_count,
            COALESCE(SUM(ABS(qty_kg)), 0) as total_kg
        FROM fact_inventory
        {where_sql}
        GROUP BY plant_code
        ORDER BY total_kg DESC
    """), params).fetchall()
    
    return [
        {
            "plant_code": str(r[0]) if r[0] else '',
            "item_count": int(r[1] or 0),
            "total_kg": float(r[2] or 0)
        }
        for r in results
    ]


# ========== NEW VISUAL INTELLIGENCE ENDPOINTS ==========

@router.get("/abc-analysis")
async def get_abc_analysis(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get ABC velocity analysis for inventory optimization
    
    Query Params:
        - start_date: Start of analysis period (defaults to 90 days ago)
        - end_date: End of analysis period (defaults to today)
    
    Returns: List of materials with stock_kg, velocity_score, abc_class
    """
    from src.core.inventory_analytics import InventoryAnalytics
    from datetime import datetime
    
    analytics = InventoryAnalytics(db)
    
    # Parse date strings to date objects
    start = datetime.fromisoformat(start_date).date() if start_date else None
    end = datetime.fromisoformat(end_date).date() if end_date else None
    
    result = analytics.get_abc_analysis(start_date=start, end_date=end)
    
    return [item.dict() for item in result]


@router.get("/top-movers-and-dead-stock")
async def get_top_movers_and_dead_stock(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, ge=5, le=20, description="Number of items per list"),
    category: str = Query('ALL_CORE', description="Material category: ALL_CORE, FG, SFG, RM"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get actionable inventory insights: Top Movers vs Dead Stock.
    
    Query Params:
        - start_date: Start of analysis period (defaults to 90 days ago)
        - end_date: End of analysis period (defaults to today)
        - limit: Number of items per list (default 10)
        - category: Material type filter (default: ALL_CORE)
            - ALL_CORE: Finish Goods (10) + Semi-Finish (12) + Raw Materials (15)
            - FG: Finish Goods only (prefix 10)
            - SFG: Semi-Finish Goods only (prefix 12)
            - RM: Raw Materials only (prefix 15)
    
    Returns: 
        {
            "top_movers": [items with highest velocity],
            "dead_stock": [items with high stock but zero velocity]
        }
    """
    from src.core.inventory_analytics import InventoryAnalytics
    from datetime import datetime
    
    analytics = InventoryAnalytics(db)
    
    # Parse date strings to date objects
    start = datetime.fromisoformat(start_date).date() if start_date else None
    end = datetime.fromisoformat(end_date).date() if end_date else None
    
    top_movers, dead_stock = analytics.get_top_movers_and_dead_stock(
        start_date=start,
        end_date=end,
        limit=limit,
        category=category
    )
    
    return {
        "top_movers": [item.dict() for item in top_movers],
        "dead_stock": [item.dict() for item in dead_stock]
    }
